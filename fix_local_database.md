# Local Database Migration Guide

## Problem
Your local SQLite database is missing some columns that were added to the WMS models, causing the error:
```
no such column: grpo_documents.supplier_code
```

## Solution
Choose one of the following solutions based on your preference:

## Steps

### Option 1: Database Reset (Recommended - Easy & Fast)
**⚠️ This will delete all existing data!**

1. **Stop your local Flask application** if it's running
2. **Navigate to your project directory** in terminal/command prompt
3. **Run the reset script:**
   ```bash
   python reset_database.py
   ```
4. **Restart your Flask application**
5. **Login with:** Username: `admin`, Password: `admin123`

### Option 2: Database Migration (Preserves Data)
1. **Stop your local Flask application** if it's running
2. **Navigate to your project directory** in terminal/command prompt
3. **Run the migration script:**
   ```bash
   python migrate_database.py
   ```
4. **Restart your Flask application**

### Option 3: Manual Database Recreation
If the migration script doesn't work, you can recreate the database:

1. **Stop your Flask application**
2. **Delete the existing database file:**
   - Look for `instance/database.db` or similar in your project
   - Delete this file (make a backup first if you have important data)
3. **Restart your Flask application**
   - The database will be recreated with the correct schema

### Option 3: Use PostgreSQL Locally
For better compatibility, consider switching to PostgreSQL locally:

1. **Install PostgreSQL** on your local machine
2. **Create a database** for the WMS application
3. **Update your environment variables:**
   ```
   DATABASE_URL=postgresql://username:password@localhost/wms_db
   ```
4. **Restart your application**

## What the Migration Script Does
- Creates a backup of your current database
- Adds missing columns to `grpo_documents` table:
  - `supplier_code` (VARCHAR(50))
  - `supplier_name` (VARCHAR(200))
  - `po_date` (DATETIME)
  - `po_total` (FLOAT)
  - `qc_user_id` (INTEGER)
  - `qc_notes` (TEXT)
  - `draft_or_post` (VARCHAR(10))

- Adds missing columns to `grpo_items` table:
  - `po_line_number` (INTEGER)
  - `po_quantity` (FLOAT)
  - `open_quantity` (FLOAT)
  - `unit_price` (FLOAT)
  - `supplier_barcode` (VARCHAR(100))
  - `generated_barcode` (VARCHAR(100))
  - `barcode_printed` (BOOLEAN)
  - `qc_status` (VARCHAR(20))
  - `qc_notes` (TEXT)

## Verification
After running the migration, your dashboard should load without errors and you should see:
- Enhanced GRPO functionality with supplier information
- QC approval workflow features
- Barcode management capabilities

## Support
If you continue to have issues after running the migration, please share:
1. The output from the migration script
2. Your current database configuration
3. Any error messages you see