"""Логика майнера: запуск движка XMRig, статистика, защита телефона."""
import json
import re
import subprocess
import time
import urllib.request

# ---------- НАСТРОЙКИ ----------
POOL = "pool.supportxmr.com:3333"
HTTP_PORT = 18088

# Комиссия разработчика. Пока DEV_WALLET пустой, комиссии нет.
# Впиши сюда СВОЙ адрес Monero, и приложение будет майнить на него
# FEE_PERCENT % времени. Пользователь видит это в приложении.
DEV_WALLET = "45ZFWaKxc8f7VbKsJ6woT6G2D1zow4ngeY4MDnLsEXjPbV1r417geByg4yQkMSN18C7JrQuXQpXvKU6MVn8YQTg7JtH2XGP"
FEE_PERCENT = 5
FEE_CYCLE = 1200  # секунд в одном круге (20 минут)

TEMP_MAX = 42.0   # °C: выше этого майнинг сам остановится
BATTERY_MIN = 15  # %: ниже этого без зарядки майнинг остановится
# --------------------------------

_B58 = "1-9A-HJ-NP-Za-km-z"
WALLET_RE = re.compile(r"^[48][%s]{94}$|^4[%s]{105}$" % (_B58, _B58))


def is_valid_wallet(text):
    return bool(WALLET_RE.match(text.strip()))


def safety_reason(bat):
    """bat: словарь из device.battery() или None. Возвращает причину остановки или None."""
    if not bat:
        return None
    if bat["temp"] >= TEMP_MAX:
        return "Телефон нагрелся (%d°C)" % round(bat["temp"])
    if bat["level"] < BATTERY_MIN and not bat["charging"]:
        return "Низкий заряд батареи"
    return None


def fee_seconds():
    return FEE_CYCLE * FEE_PERCENT / 100.0


class Miner:
    def __init__(self, engine, clock=time.time):
        self.engine = engine
        self.clock = clock
        self.proc = None
        self.wallet = None
        self.percent = 50
        self.cycle_start = 0
        self.fee_mode = False

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def _launch(self, wallet):
        self._kill()
        args = [
            self.engine, "-o", POOL, "-u", wallet, "-p", "phone",
            "-a", "rx/0", "-k", "--randomx-mode=light", "--no-color",
            "--http-host", "127.0.0.1", "--http-port", str(HTTP_PORT),
            "--cpu-max-threads-hint", str(self.percent),
        ]
        self.proc = subprocess.Popen(
            args, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _kill(self):
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()

    def start(self, wallet, percent):
        self.wallet = wallet.strip()
        self.percent = int(percent)
        self.cycle_start = self.clock()
        self.fee_mode = False
        self._launch(self.wallet)

    def stop(self):
        self._kill()

    def tick(self):
        """Вызывать каждые пару секунд. Переключает комиссию. False, если движок упал."""
        if not self.running:
            return False
        if DEV_WALLET and FEE_PERCENT > 0:
            pos = (self.clock() - self.cycle_start) % FEE_CYCLE
            want_fee = pos >= FEE_CYCLE - fee_seconds()
            if want_fee != self.fee_mode:
                self.fee_mode = want_fee
                self._launch(DEV_WALLET if want_fee else self.wallet)
        return True

    def stats(self):
        try:
            url = "http://127.0.0.1:%d/1/summary" % HTTP_PORT
            with urllib.request.urlopen(url, timeout=1.5) as r:
                d = json.loads(r.read().decode())
            hr = (d.get("hashrate") or {}).get("total") or [0]
            return {
                "hashrate": float(hr[0] or 0),
                "shares": int((d.get("results") or {}).get("shares_good", 0)),
                "fee": self.fee_mode,
            }
        except Exception:
            return None
