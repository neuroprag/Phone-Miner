MINER: легальный майнер Monero для телефона
(майнит на кошелёк пользователя, включается кнопкой)

== 1. Распаковка ==
   unzip phone-miner.zip
   cd phone-miner

== 2. Окружение (то, что уже ловили раньше) ==
   source ~/bvenv/bin/activate
   pip install buildozer cython==0.29.36 appdirs sh colorama jinja2 build toml packaging setuptools
   export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
   export PATH=$JAVA_HOME/bin:$PATH
(если ~/bvenv нет: /usr/bin/python3 -m venv ~/bvenv, и потом source)

== 3. Сборка приложения ==
   buildozer -v android debug 2>&1 | tee log.txt
APK будет в папке bin/. Без движка приложение откроется,
но на кнопку скажет «Нет движка XMRig».

== 4. Движок XMRig (без него майнинга нет) ==
   bash build_xmrig.sh
Скрипт экспериментальный, я его не мог проверить.
Если получится, появится libs/arm64-v8a/libxmrig.so.
Тогда в buildozer.spec убери # у строки android.add_libs_arm64_v8a
и пересобери APK (шаг 3).
Если скрипт упал, пришли последние строки ошибки.

== Настройки ==
miner.py вверху: пул, порог температуры (TEMP_MAX), порог заряда
(BATTERY_MIN), комиссия разработчика (DEV_WALLET + FEE_PERCENT).
Пока DEV_WALLET пустой, комиссии нет. Если впишешь свой адрес,
комиссия честно пишется в приложении.
XMRig сам берёт 1% для своих авторов, это его стандартная настройка.

Иконка: замени icon.png на свою (квадрат 512x512).
