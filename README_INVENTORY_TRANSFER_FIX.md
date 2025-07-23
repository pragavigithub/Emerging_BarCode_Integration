# Inventory Transfer MySQL Database Fix

## Issue Fixed
**Error**: `Unknown column 'inventory_transfer_items.qc_status' in 'field list'`

**Root Cause**: The MySQL database is missing QC-related columns that were added to the application models but not migrated to the database.

## Solution

### Single Migration Script
Run this one command to fix the database:

```bash
python mysql_inventory_transfer_migration.py
```

Or use the runner script:
```bash
python run_mysql_inventory_migration.py
```

## What the Migration Does

### 1. Fixes `inventory_transfer_items` Table
Adds missing column:
- `qc_status` VARCHAR(20) DEFAULT 'pending'

### 2. Fixes `inventory_transfers` Table  
Adds missing QC approval columns:
- `qc_approver_id` INT (with foreign key to users table)
- `qc_approved_at` DATETIME
- `qc_notes` TEXT

### 3. Verification
- Checks all columns exist after migration
- Verifies foreign key constraints
- Confirms database structure matches models

## Environment Setup

### Set MySQL Connection Variables:
```bash
# Set these environment variables
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=wms_database
export MYSQL_PORT=3306
```

### Or edit the script directly:
Update the connection details in `mysql_inventory_transfer_migration.py`

## Expected Output

```
🚀 MySQL Inventory Transfer Migration Script
============================================================
Started at: 2025-07-23 14:30:45.123456

✅ Successfully connected to MySQL database
🔍 Checking inventory_transfer_items table structure...
➕ Adding column: qc_status
✅ Added column: qc_status
🔍 Checking inventory_transfers table structure...
➕ Adding column: qc_approver_id
✅ Added column: qc_approver_id
➕ Adding column: qc_approved_at
✅ Added column: qc_approved_at
➕ Adding column: qc_notes
✅ Added column: qc_notes
✅ Added foreign key constraint for qc_approver_id
🔍 Verifying migration...
✅ inventory_transfer_items table has all required columns
✅ inventory_transfers table has all required columns
🎉 Migration verification PASSED!

============================================================
🎉 MIGRATION COMPLETED SUCCESSFULLY!
✅ inventory_transfer_items table updated with QC columns
✅ inventory_transfers table updated with QC approval columns
✅ All foreign key constraints applied

Your inventory transfer functionality should now work correctly.
```

## After Migration

1. **Restart your Flask application**
2. **Test inventory transfer functionality**
3. **Verify QC workflow works correctly**

## Troubleshooting

### Connection Issues
```
❌ Failed to connect to MySQL: Access denied for user
```
**Fix**: Check username, password, and database name

### Permission Issues  
```
❌ Error migrating: Table 'wms_database.inventory_transfer_items' doesn't exist
```
**Fix**: Ensure you're connected to the correct database

### Already Applied
```
⚡ Column qc_status already exists
✅ All required columns already exist
```
**Result**: No changes needed, database is already up to date

## Database Schema After Migration

### inventory_transfer_items
- id (Primary Key)
- inventory_transfer_id (Foreign Key)
- item_code
- item_name  
- quantity
- unit_of_measure
- from_warehouse_code
- to_warehouse_code
- from_bin
- to_bin
- batch_number
- serial_number
- expiry_date
- unit_price
- total_value
- **qc_status** ← **ADDED**
- base_entry
- base_line
- sap_line_number
- created_at
- updated_at

### inventory_transfers
- id (Primary Key)
- transfer_request_number
- from_warehouse
- to_warehouse
- status
- user_id (Foreign Key)
- **qc_approver_id** ← **ADDED** (Foreign Key to users)
- **qc_approved_at** ← **ADDED**
- **qc_notes** ← **ADDED**
- created_at
- updated_at

The inventory transfer error should be completely resolved after running this migration.