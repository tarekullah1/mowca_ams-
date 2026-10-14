@echo off
title BioTime Sync Daemon
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python sync_worker.py --loop --interval 600
pause
