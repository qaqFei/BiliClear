@echo off

cd ..

python -m venv release-ven

.\release-ven\Scripts\pip install -r requirements.txt
.\release-ven\Scripts\pip install pyinstaller

.\release-ven\Scripts\pyinstaller biliclear.py -i .\res\icon.ico
.\release-ven\Scripts\pyinstaller biliclear_gui_webui.py -i .\res\icon.ico
.\release-ven\Scripts\pyinstaller biliclear_gui_qt.py -i .\res\icon.ico

xcopy .\dist\biliclear\* .\ /s /e /y
xcopy .\dist\biliclear_gui_webui\* .\ /s /e /y
xcopy .\dist\biliclear_gui_qt\* .\ /s /e /y

rmdir /s /q release-ven
rmdir /s /q build
rmdir /s /q dist
del biliclear.spec
del biliclear_gui_webui.spec
del biliclear_gui_qt.spec