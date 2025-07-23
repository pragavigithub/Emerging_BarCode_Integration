# MySQL Database Migration Guide

## Quick Fix for "Unknown column 'qc_status'" Error

You're getting this error because your MySQL database is missing required columns that were added in recent updates.

## Solution: Easy One-Click Migration

### Option 1: Windows Batch File (Recommended)

Simply double-click or run:

```batch
run_mysql_migration.bat
```

This will:
1. Prompt you for MySQL credentials
2. Set environment variables automatically
3. Run the migration script

### Option 2: Python Setup Script

```bash
python setup_mysql_env.py
```

### Option 3: Manual Environment Variables

If you prefer to set environment variables manually:

```bash
# Windows Command Prompt
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=your_database_name
python complete_mysql_migration.py

# Windows PowerShell
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"  
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="your_database_name"
python complete_mysql_migration.py
```

## What This Script Does

✅ **Creates all required tables** if they don't exist  
✅ **Adds missing columns** to existing tables:
- `inventory_transfer_items.qc_status`
- `inventory_transfer_items.qc_notes`  
- `inventory_transfer_items.serial_number`
- `grpo_documents.po_date`
- `grpo_documents.po_total`
- `grpo_documents.notes`
- `grpo_items.serial_number`
- `inventory_transfers.transfer_request_number`
- `inventory_transfers.from_warehouse`
- `inventory_transfers.to_warehouse`

✅ **Creates default data**:
- Default branch (BR001)
- Admin user (username: admin, password: admin123)

## After Migration

1. **Restart your Flask application**
2. **Test the inventory transfer screen** - the error should be resolved
3. **Login with**: username `admin`, password `admin123`

## Troubleshooting

If you still get errors after migration:

1. **Check your environment variables** are set correctly
2. **Verify MySQL connection** by running the script again
3. **Check the migration output** for any error messages

## Clean Start (Optional)

If you want to start fresh, you can drop all tables and re-run the migration:

```sql
-- Connect to your MySQL database and run:
DROP TABLE IF EXISTS barcode_labels;
DROP TABLE IF EXISTS inventory_count_items;
DROP TABLE IF EXISTS inventory_counts;
DROP TABLE IF EXISTS pick_list_items;
DROP TABLE IF EXISTS pick_lists;
DROP TABLE IF EXISTS inventory_transfer_items;
DROP TABLE IF EXISTS inventory_transfers;
DROP TABLE IF EXISTS grpo_items;
DROP TABLE IF EXISTS grpo_documents;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS users;
```

Then run: `python complete_mysql_migration.py`

---

**Note**: All old migration files have been removed. Use only `complete_mysql_migration.py` going forward.