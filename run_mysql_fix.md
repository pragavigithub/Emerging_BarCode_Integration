# Quick MySQL Database Fix

## Problem
The application is trying to access the `notes` column in the `grpo_documents` table, but it doesn't exist in your MySQL database.

## Solution Options

### Option 1: Run SQL Script Directly (Recommended)
1. Open MySQL command line or MySQL Workbench
2. Connect to your `wms_db` database
3. Run the `manual_mysql_fix.sql` file:

```sql
SOURCE manual_mysql_fix.sql;
```

OR copy and paste the contents of `manual_mysql_fix.sql` into your MySQL client.

### Option 2: Use Python Script
1. Make sure your environment variables are set:
   ```bash
   export MYSQL_HOST=localhost
   export MYSQL_PORT=3306
   export MYSQL_USER=root
   export MYSQL_PASSWORD=your_password
   export MYSQL_DATABASE=wms_db
   ```

2. Run the Python migration script:
   ```bash
   python fix_mysql_schema.py
   ```

### Option 3: Manual Commands
If you prefer to run commands one by one:

```sql
USE wms_db;
ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL;
ALTER TABLE grpo_documents ADD COLUMN qc_notes TEXT NULL;
ALTER TABLE grpo_documents ADD COLUMN draft_or_post VARCHAR(10) DEFAULT 'draft';
```

## Verification
After running the fix, verify the column was added:

```sql
DESCRIBE grpo_documents;
```

You should see the `notes` column in the table structure.

## What This Fixes
- ✓ Adds missing `notes` column to `grpo_documents` table
- ✓ Adds other essential columns for barcode functionality
- ✓ Creates missing `barcode_labels` and `branches` tables
- ✓ Resolves the SQLAlchemy "Unknown column" error

## Next Steps
After running this fix, your application should work without the database error.