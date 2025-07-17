@echo off
echo ========================================
echo  WMS DATABASE SETUP AND FIX
echo ========================================
echo.

echo Option 1: Setup MySQL Environment (RECOMMENDED)
echo Option 2: Complete MySQL Migration
echo Option 3: Run inventory transfer fix (MySQL/PostgreSQL/SQLite)
echo Option 4: Delete SQLite database and recreate
echo.

set /p choice="Enter your choice (1, 2, 3, or 4): "

if "%choice%"=="1" (
    echo Setting up MySQL environment...
    python setup_mysql_env.py
) else if "%choice%"=="2" (
    echo Running complete MySQL migration...
    python mysql_migration.py
) else if "%choice%"=="3" (
    echo Running inventory transfer fix...
    python fix_inventory_transfer_schema.py
) else if "%choice%"=="4" (
    echo Deleting old SQLite database...
    if exist instance\warehouse.db (
        del instance\warehouse.db
        echo Database deleted: instance\warehouse.db
    )
    if exist warehouse.db (
        del warehouse.db
        echo Database deleted: warehouse.db
    )
    echo.
    echo SQLite database reset complete!
    echo Please restart your Flask application now.
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo ========================================
echo  SETUP COMPLETE
echo ========================================
pause