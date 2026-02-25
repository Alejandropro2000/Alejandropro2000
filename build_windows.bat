@echo off
REM Genera ejecutable instalable para Windows usando PyInstaller
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --onefile --name InfoConfidencialPY app.py

echo.
echo Listo. Ejecutable generado en: dist\InfoConfidencialPY.exe
pause
