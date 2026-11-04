import json
import os
import threading

from kivy import kivy_data_dir
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput

import device
import miner as M

# ---------- ДИЗАЙН ----------
BG = (0.043, 0.051, 0.063, 1)
CARD = (0.075, 0.086, 0.106, 1)
LINE = (0.16, 0.18, 0.22, 1)
TEXT = (0.93, 0.94, 0.96, 1)
MUTED = (0.50, 0.53, 0.58, 1)
ACCENT = (0.24, 0.86, 0.59, 1)
WARN = (1.00, 0.45, 0.40, 1)

_mono = os.path.join(kivy_data_dir, "fonts", "RobotoMono-Regular.ttf")
MONO = _mono if os.path.exists(_mono) else "Roboto"

Window.clearcolor = BG


def hexc(c):
    return "%02x%02x%02x" % tuple(int(x * 255) for x in c[:3])


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*CARD)
            self._bg = RoundedRectangle(radius=[dp(16)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._bg.pos, self._bg.size = self.pos, self.size


class Stat(Card):
    def __init__(self, caption, **kw):
        super().__init__(orientation="vertical", padding=(dp(14), dp(10)), spacing=dp(2), **kw)
        cap = Label(text=caption, font_size="11sp", color=MUTED, halign="left", valign="bottom")
        cap.bind(size=lambda i, s: setattr(i, "text_size", s))
        self.val = Label(text="–", font_size="19sp", font_name=MONO, color=TEXT,
                         halign="left", valign="top")
        self.val.bind(size=lambda i, s: setattr(i, "text_size", s))
        self.add_widget(cap)
        self.add_widget(self.val)

    def set(self, text, color=TEXT):
        self.val.text = text
        self.val.color = color


class PowerButton(FloatLayout):
    running = BooleanProperty(False)
    glow = NumericProperty(0)

    def __init__(self, on_toggle, **kw):
        super().__init__(**kw)
        self.on_toggle = on_toggle
        self._down = False
        self.label = Label(text="СТАРТ", font_size="18sp", bold=True, color=MUTED)
        self.add_widget(self.label)
        self.bind(pos=self.redraw, size=self.redraw, running=self.redraw, glow=self.redraw)

    def redraw(self, *a):
        self.canvas.before.clear()
        d = min(self.width, self.height) * 0.78
        cx, cy = self.center
        with self.canvas.before:
            if self.running:
                g = dp(26) * self.glow
                Color(ACCENT[0], ACCENT[1], ACCENT[2], 0.07 + 0.10 * self.glow)
                Ellipse(pos=(cx - d / 2 - g, cy - d / 2 - g), size=(d + 2 * g, d + 2 * g))
            Color(*CARD)
            Ellipse(pos=(cx - d / 2, cy - d / 2), size=(d, d))
            Color(*(ACCENT if self.running else LINE))
            Line(circle=(cx, cy, d / 2), width=dp(1.6))

    def on_running(self, inst, val):
        Animation.cancel_all(self, "glow")
        if val:
            self.label.text, self.label.color = "СТОП", ACCENT
            a = Animation(glow=1, d=1.5, t="in_out_sine") + Animation(glow=0, d=1.5, t="in_out_sine")
            a.repeat = True
            a.start(self)
        else:
            self.label.text, self.label.color = "СТАРТ", MUTED
            self.glow = 0

    def on_touch_down(self, touch):
        self._down = self.collide_point(*touch.pos)
        return self._down

    def on_touch_up(self, touch):
        hit = self._down and self.collide_point(*touch.pos)
        self._down = False
        if hit:
            self.on_toggle()
            return True
        return False


class Root(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", padding=(dp(24), dp(28), dp(24), dp(20)),
                         spacing=dp(12), **kw)
        self.app = app
        self.engine = device.engine_path()
        self.miner = M.Miner(self.engine) if self.engine else None
        self.busy = False

        title = Label(text="MINER", font_size="13sp", color=MUTED, bold=True,
                      size_hint_y=None, height=dp(24), halign="left")
        title.bind(size=lambda i, s: setattr(i, "text_size", s))
        self.add_widget(title)

        self.power = PowerButton(self.toggle, size_hint_y=0.40)
        self.add_widget(self.power)

        self.rate = Label(font_size="44sp", font_name=MONO, markup=True, color=TEXT,
                          size_hint_y=None, height=dp(62))
        self.add_widget(self.rate)
        self.set_rate(0)

        self.status = Label(text="Остановлено", font_size="14sp", color=MUTED,
                            size_hint_y=None, height=dp(24))
        self.add_widget(self.status)

        row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
        self.s_temp = Stat("ТЕМПЕРАТУРА")
        self.s_bat = Stat("ЗАРЯД")
        self.s_shares = Stat("ШАРЫ")
        for s in (self.s_temp, self.s_bat, self.s_shares):
            row.add_widget(s)
        self.add_widget(row)

        wallet_card = Card(size_hint_y=None, height=dp(52), padding=(dp(16), dp(4)))
        self.wallet = TextInput(
            text=app.cfg.get("wallet", ""), hint_text="Адрес вашего кошелька Monero",
            multiline=False, write_tab=False, font_size="14sp",
            background_color=(0, 0, 0, 0), foreground_color=TEXT,
            hint_text_color=MUTED, cursor_color=ACCENT,
            padding=(0, dp(14), 0, 0))
        wallet_card.add_widget(self.wallet)
        self.add_widget(wallet_card)

        load_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))
        self.load_label = Label(text="Нагрузка 50%", font_size="13sp", color=MUTED,
                                size_hint_x=None, width=dp(120), halign="left")
        self.load_label.bind(size=lambda i, s: setattr(i, "text_size", s))
        self.slider = Slider(min=25, max=75, step=5, value=app.cfg.get("load", 50),
                             value_track=True, value_track_color=ACCENT)
        self.slider.bind(value=self.on_load)
        self.on_load(self.slider, self.slider.value)
        load_row.add_widget(self.load_label)
        load_row.add_widget(self.slider)
        self.add_widget(load_row)

        note = "Всё добытое идёт на ваш кошелёк."
        if M.DEV_WALLET and M.FEE_PERCENT:
            note += " Комиссия разработчика: %d%% времени." % M.FEE_PERCENT
        note += "\nРаботает, пока приложение открыто."
        foot = Label(text=note, font_size="11sp", color=MUTED, halign="center",
                     size_hint_y=None, height=dp(34))
        foot.bind(size=lambda i, s: setattr(i, "text_size", (s[0], None)))
        self.add_widget(foot)

        Clock.schedule_interval(self.refresh, 3)
        Clock.schedule_once(self.refresh, 0.5)

    # ---------- помощники ----------
    def set_rate(self, v):
        self.rate.text = "%.1f [size=16sp][color=%s]H/s[/color][/size]" % (v, hexc(MUTED))

    def say(self, text, color=MUTED):
        self.status.text, self.status.color = text, color

    def on_load(self, inst, val):
        self.load_label.text = "Нагрузка %d%%" % val

    # ---------- старт / стоп ----------
    def toggle(self):
        if self.power.running:
            self.stop("Остановлено")
        else:
            self.start()

    def start(self):
        if not self.miner:
            self.say("Нет движка XMRig (см. README)", WARN)
            return
        wallet = self.wallet.text.strip()
        if not M.is_valid_wallet(wallet):
            self.say("Проверь адрес кошелька Monero", WARN)
            return
        reason = M.safety_reason(device.battery())
        if reason:
            self.say(reason, WARN)
            return
        self.app.cfg.update(wallet=wallet, load=int(self.slider.value))
        self.app.save_cfg()
        try:
            self.miner.start(wallet, self.slider.value)
        except Exception as e:
            self.say("Не удалось запустить: %s" % e, WARN)
            return
        device.keep_awake(True)
        self.power.running = True
        self.say("Майнинг идёт", ACCENT)

    def stop(self, msg, color=MUTED):
        if self.miner:
            self.miner.stop()
        device.keep_awake(False)
        self.power.running = False
        self.set_rate(0)
        self.say(msg, color)

    # ---------- обновление раз в 3 секунды ----------
    def refresh(self, *a):
        bat = device.battery()
        if bat:
            hot = bat["temp"] >= M.TEMP_MAX - 3
            self.s_temp.set("%d°C" % round(bat["temp"]), WARN if hot else TEXT)
            self.s_bat.set("%d%%" % bat["level"])
        if not self.power.running:
            return
        reason = M.safety_reason(bat)
        if reason:
            self.stop("Остановлено: " + reason, WARN)
            return
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            alive = self.miner.tick()
            st = self.miner.stats() if alive else None
        except Exception:
            alive, st = False, None
        Clock.schedule_once(lambda dt: self._apply(alive, st))

    def _apply(self, alive, st):
        self.busy = False
        if not self.power.running:
            return
        if not alive:
            self.stop("Движок остановился", WARN)
            return
        if st:
            self.set_rate(st["hashrate"])
            self.s_shares.set(str(st["shares"]))
            self.say("Комиссия разработчика…" if st["fee"] else "Майнинг идёт", ACCENT)
        else:
            self.say("Подключаюсь к пулу…", MUTED)


class MinerApp(App):
    title = "Miner"

    def build(self):
        self.cfg_path = os.path.join(self.user_data_dir, "config.json")
        try:
            with open(self.cfg_path) as f:
                self.cfg = json.load(f)
        except Exception:
            self.cfg = {}
        self.root_widget = Root(self)
        return self.root_widget

    def save_cfg(self):
        try:
            with open(self.cfg_path, "w") as f:
                json.dump(self.cfg, f)
        except Exception:
            pass

    def on_pause(self):
        return True

    def on_stop(self):
        if self.root_widget.miner:
            self.root_widget.miner.stop()


if __name__ == "__main__":
    MinerApp().run()
