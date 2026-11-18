@echo off
powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process -Filter ""Name='pythonw.exe'"" | Where-Object { $_.CommandLine -like '*HandGestureLauncher*main.py*' }; $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
