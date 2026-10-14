@echo off
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python sync_worker.py --once
