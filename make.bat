@echo off
set QT_QPA_PLATFORM_PLUGIN_PATH=D:\anaconda3\Lib\site-packages\PySide2\plugins
pyinstaller -i AuraProII.ico -p D:\anaconda3\envs\auraproii\lib\site-packages\PyQt5\Qt\bin -w -F src\AuraProII.py
