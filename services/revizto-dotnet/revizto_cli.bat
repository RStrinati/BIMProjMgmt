@echo off
REM Revizto Data Exporter CLI Batch Script
REM Usage examples:
REM   revizto_cli.bat status
REM   revizto_cli.bat list-projects
REM   revizto_cli.bat export 429b27f4-4359-40d6-a526-c2ac8374a3c9
REM   revizto_cli.bat refresh

cd /d "%~dp0"
.\publish\ReviztoDataExporter.exe %*