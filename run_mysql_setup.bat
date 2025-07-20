@echo off
echo =====================================
echo WMS MySQL Database Setup
echo =====================================
echo.
echo This script will set up MySQL database for WMS application
echo Make sure MySQL is installed and running on your system
echo.
pause

echo Installing required Python packages...
pip install mysql-connector-python pymysql

echo.
echo Running MySQL setup script...
python setup_mysql_local.py

echo.
echo Setup completed!
echo You can now run your WMS application with MySQL database
echo.
pause