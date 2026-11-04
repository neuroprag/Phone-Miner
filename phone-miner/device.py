"""Работа с Android: батарея, температура, экран, путь к движку. На ПК всё безопасно молчит."""
import os


def _activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity


def battery():
    try:
        from jnius import autoclass
        ctx = _activity()
        Intent = autoclass("android.content.Intent")
        IntentFilter = autoclass("android.content.IntentFilter")
        BM = autoclass("android.os.BatteryManager")
        i = ctx.registerReceiver(None, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        level = i.getIntExtra(BM.EXTRA_LEVEL, -1)
        scale = i.getIntExtra(BM.EXTRA_SCALE, 100)
        temp = i.getIntExtra(BM.EXTRA_TEMPERATURE, 0) / 10.0
        plugged = i.getIntExtra(BM.EXTRA_PLUGGED, 0)
        return {"level": int(level * 100 / scale) if level >= 0 else 100,
                "temp": temp, "charging": plugged != 0}
    except Exception:
        return None


try:
    from android.runnable import run_on_ui_thread

    @run_on_ui_thread
    def keep_awake(on):
        try:
            win = _activity().getWindow()
            (win.addFlags if on else win.clearFlags)(128)  # FLAG_KEEP_SCREEN_ON
        except Exception:
            pass
except Exception:
    def keep_awake(on):
        pass


def engine_path():
    candidates = []
    try:
        candidates.append(os.path.join(
            _activity().getApplicationInfo().nativeLibraryDir, "libxmrig.so"))
    except Exception:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    candidates += [os.path.join(here, "xmrig"), "./xmrig"]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None
