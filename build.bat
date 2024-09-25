rmdir /s /q dist
:: pyinstaller player.py --onefile --icon icons\icon.ico
pyinstaller player.py --onefile
copy README.md dist\README.md
copy options.conf dist\options.conf
xcopy /s /e /h /I /q skins dist\skins