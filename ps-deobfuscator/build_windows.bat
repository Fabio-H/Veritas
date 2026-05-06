@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo  Veritas / ps-deobfuscator - build Windows
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH.
  pause
  exit /b 1
)

echo [1/2] pip install ".[gui,dev,build]" ...
pip install -q ".[gui,dev,build]"
if errorlevel 1 (
  echo [ERRO] pip install falhou.
  pause
  exit /b 1
)

echo [2/2] scripts\build_exe.py ^(testes + PyInstaller + copia/zip para ..\release\^) ...
python scripts\build_exe.py
if errorlevel 1 (
  echo [ERRO] build_exe.py falhou.
  pause
  exit /b 1
)

set "REL=%~dp0..\release\ps-deobfuscator-gui\ps-deobfuscator-gui.exe"
set "DIST=%~dp0dist\ps-deobfuscator-gui\ps-deobfuscator-gui.exe"

echo.
echo ============================================
echo  CONCLUIDO
echo  Copia de acesso: %REL%
echo  Build PyInstaller: %DIST%
echo  ZIP versionado: ..\release\Veritas-vX.Y.Z-windows.zip
echo ============================================
if exist "%REL%" (dir "%REL%") else (echo Aviso: copia em release nao encontrada.)

echo.
echo A abrir o programa em 2 segundos ^(copia release^)...
timeout /t 2 >nul
if exist "%REL%" (start "" "%REL%") else if exist "%DIST%" (start "" "%DIST%") else (echo Nenhum exe encontrado.)
pause
