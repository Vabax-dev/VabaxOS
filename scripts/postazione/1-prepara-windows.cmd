@echo off
rem Starts prepara-windows.ps1 with administrator rights (ADR-0013).
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -NoExit -File \"%~dp0prepara-windows.ps1\"'"
