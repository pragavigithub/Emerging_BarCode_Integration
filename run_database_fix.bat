@echo off
echo ========================================
echo  INVENTORY TRANSFER DATABASE FIX
echo ========================================
echo.

echo Option 1: Delete SQLite database and recreate (RECOMMENDED for SQLite)
echo Option 2: Run migration script (MySQL/PostgreSQL/SQLite)
echo Option 3: Run quick fix script (MySQL/PostgreSQL/SQLite)
echo Option 4: Setup MySQL database (NEW!)
echo.

set /p choice="Enter your choice (1, 2, 3, or 4): "

if "%choice%"=="1" (
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
    echo The database will be recreated with all new columns.
) else if "%choice%"=="2" (
    echo Running migration script (supports MySQL/PostgreSQL/SQLite)...
    python migrate_inventory_transfers.py
) else if "%choice%"=="3" (
    echo Running quick fix script (supports MySQL/PostgreSQL/SQLite)...
    python fix_inventory_transfer_schema.py
) else if "%choice%"=="4" (
    echo Setting up MySQL database...
    python setup_mysql_local.py
    echo.
    echo After MySQL setup, run the migration:
    python migrate_inventory_transfers.py
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo ========================================
echo  FIX COMPLETE
echo ========================================
pause