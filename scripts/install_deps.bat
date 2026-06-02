@echo off
setlocal
cd /d %~dp0..

if not exist .venv (
  python -m venv .venv
)

echo [1/2] Installing base dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt

echo [2/2] Installing locked dependencies...
.venv\Scripts\pip.exe install -r requirements-lock.txt

echo Done.
