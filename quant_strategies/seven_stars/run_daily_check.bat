@echo off
cd /d "%~dp0"
"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0local_etf_quant_bot.py" --now >> "%~dp0run.log" 2>&1
