# 🚨 URGENT MySQL Database Fix

## The Problem
Your MySQL database exists but has wrong column structure. The tables were created without the proper schema that your Flask models expect.

## ✅ QUICK FIX (Run this now):

```bash
python quick_mysql_fix.py
```

This will:
1. Drop and recreate all tables with correct structure
2. Add missing columns (`name`, `first_name`, `last_name`, etc.)
3. Insert default branch and admin user
4. Fix all schema mismatches

## Why the Error Happened

Your previous setup created tables but missed columns like:
- `branches.name` 
- `users.first_name`
- `users.last_name` 
- And many others

## Alternative Manual Fix

If the script doesn't work, run this in MySQL directly:

```sql
USE wms_db_dev;

-- Fix branches table
DROP TABLE IF EXISTS branches;
CREATE TABLE branches (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    manager_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default branch
INSERT INTO branches (id, name, address, is_active, is_default) 
VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE);

-- Fix users table
ALTER TABLE users ADD COLUMN first_name VARCHAR(50);
ALTER TABLE users ADD COLUMN last_name VARCHAR(50);
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
ALTER TABLE users ADD COLUMN branch_id VARCHAR(10);
ALTER TABLE users ADD COLUMN branch_name VARCHAR(100);
ALTER TABLE users ADD COLUMN default_branch_id VARCHAR(10);
-- (Additional columns listed in quick_mysql_fix.py)
```

## What Happens After Fix

1. `python main.py` will work without errors
2. GRPO Add Item buttons will function properly
3. Inventory Transfer data will load correctly
4. Database will have proper structure for all features

## Test the Fix

After running the fix:
1. Run `python main.py`
2. Login with: username=`admin`, password=`admin123`
3. Navigate to GRPO → Create new GRPO
4. Test Add Item buttons

Your application should now work with MySQL database properly configured.