@echo off
echo ============================================================
echo    MySQL Database Migration for Windows
echo    Warehouse Management System (WMS)
echo ============================================================
echo.

echo Setting up MySQL environment and running migration...
echo.

python setup_mysql_env.py

echo.
echo Press any key to exit...
pause >nul