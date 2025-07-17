@echo off
echo ========================================
echo  INVENTORY TRANSFER DATABASE FIX
echo ========================================
echo.

echo Option 1: Delete database and recreate (RECOMMENDED)
echo Option 2: Run migration script
echo Option 3: Run quick fix script
echo.

set /p choice="Enter your choice (1, 2, or 3): "

if "%choice%"=="1" (
    echo Deleting old database...
    if exist instance\warehouse.db (
        del instance\warehouse.db
        echo Database deleted: instance\warehouse.db
    )
    if exist warehouse.db (
        del warehouse.db
        echo Database deleted: warehouse.db
    )
    echo.
    echo Database reset complete!
    echo Please restart your Flask application now.
    echo The database will be recreated with all new columns.
) else if "%choice%"=="2" (
    echo Running migration script...
    python migrate_inventory_transfers.py
) else if "%choice%"=="3" (
    echo Running quick fix script...
    python fix_inventory_transfer_schema.py
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo ========================================
echo  FIX COMPLETE
echo ========================================
pause