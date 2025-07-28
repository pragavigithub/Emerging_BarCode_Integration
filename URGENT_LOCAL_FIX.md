# URGENT: Local Database Fix Guide

## Problem
You're getting this error when trying to login:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: users.user_is_active
```

This happens because your local SQLite database schema is missing recent columns that were added to the User model.

## Quick Fix (2 steps)

### Step 1: Run the Fix Script
```bash
python fix_local_database.py
```

This script will:
- ✅ Add all missing columns to your SQLite database
- ✅ Create default admin user and branch
- ✅ Fix all schema mismatches

### Step 2: Login with Default Credentials
After running the fix script, login with:
- **Username:** admin
- **Password:** admin123

⚠️ **Important:** Change the password after first login!

## What the Script Does

The script automatically fixes these missing columns:

### Users table:
- `user_is_active` (Boolean)
- `must_change_password` (Boolean)
- `last_login` (DateTime)
- `permissions` (Text)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `first_name` (String)
- `last_name` (String)
- `role` (String)
- `branch_id` (String)
- `branch_name` (String)
- `default_branch_id` (String)

### GRPO Documents table:
- `po_date` (DateTime)
- `po_total` (Decimal)
- `notes` (Text)
- `qc_approver_id` (Integer)
- `qc_approved_at` (DateTime)
- `qc_notes` (Text)

### Inventory Transfer tables:
- `transfer_request_number` (String)
- `from_warehouse` (String)
- `to_warehouse` (String)
- `qc_status` (String)
- `qc_notes` (Text)
- `serial_number` (String)

## Alternative: Use MySQL Database

If you prefer to use MySQL for local development (as mentioned in your preferences), follow these steps:

1. Install MySQL locally
2. Run the MySQL migration script:
   ```bash
   python complete_mysql_migration.py
   ```

## After Fix

Once the fix is applied:
1. ✅ Login will work without errors
2. ✅ All WMS features will be functional
3. ✅ QR code generation will work properly
4. ✅ Database operations will complete successfully

## If You Still Have Issues

1. Check if the script ran successfully (look for "✅ Database schema fix completed successfully!")
2. Verify the `instance/warehouse.db` file exists
3. Try restarting the Flask application
4. Contact support if issues persist

This fix maintains all your existing data while adding the missing schema elements.