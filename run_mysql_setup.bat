@echo off
echo ================================================
echo MySQL Database Setup for Warehouse Management System
echo ================================================
echo.
echo This script will help you set up MySQL database
echo for your warehouse management system.
echo.
echo Prerequisites:
echo - MySQL Server installed and running
echo - Python 3.8+ installed
echo - pip package manager
echo.
pause

echo Installing required Python packages...
pip install pymysql mysql-connector-python python-dotenv

echo.
echo Starting MySQL setup...
python setup_mysql_database.py

echo.
echo Setup complete! 
echo To start the application with MySQL, restart your Flask server.
echo.
pause