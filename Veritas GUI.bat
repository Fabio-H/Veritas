@echo off
setlocal EnableExtensions
set "EXE=%~dp0release\ps-deobfuscator-gui\ps-deobfuscator-gui.exe"
if not exist "%EXE%" (
  echo [Veritas] Ainda nao ha build em release\
  echo Execute: ps-deobfuscator\build_windows.bat
  echo           ou:  cd ps-deobfuscator ^& python scripts\build_exe.py
  pause
  exit /b 1
)
start "" "%EXE%"
