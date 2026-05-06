Veritas — distribuição Windows (PyInstaller, pasta completa)
================================================================

O programa é empacotado como pasta one-folder: o executável precisa
dos ficheiros em _internal/ ao lado.

  ps-deobfuscator-gui.exe   <- atalho para este ficheiro
  _internal/                <- não apagar

Este directório é preenchido ao correr o build no projecto:
  ps-deobfuscator\scripts\build_exe.py
ou
  ps-deobfuscator\build_windows.bat

Copia final: release\ps-deobfuscator-gui\ (substituição total a cada build).
Arquivo versionado: release\Veritas-vX.Y.Z-windows.zip
