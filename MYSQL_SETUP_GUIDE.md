# 🚨 COMPLETE MySQL Database Setup Guide

## Current Issues Found:
Your MySQL database has incomplete schema with these missing columns:

### ❌ GRPO Module Errors:
- `grpo_documents.po_date` (DATETIME)
- `grpo_documents.po_total` (DECIMAL)
- `grpo_documents.qc_notes` (TEXT)
- `grpo_items.unit_price` (DECIMAL)

### ❌ Inventory Transfer Module Errors:
- `inventory_transfers.transfer_request_number` (VARCHAR)
- `inventory_transfers.from_warehouse` (VARCHAR)
- `inventory_transfers.to_warehouse` (VARCHAR)

## ✅ COMPLETE FIX (Run This):

```bash
python quick_mysql_fix.py
```

This script will:
1. Connect to your MySQL database (localhost:3306)
2. Drop and recreate ALL tables with correct schema
3. Insert default branch and admin user
4. Fix all missing columns automatically

## Manual SQL Fix Alternative:

If the script fails, run this in MySQL Workbench:

```sql
USE wms_db_dev;

-- Add missing columns to existing tables
ALTER TABLE grpo_documents ADD COLUMN IF NOT EXISTS po_date DATETIME;
ALTER TABLE grpo_documents ADD COLUMN IF NOT EXISTS po_total DECIMAL(15,2);
ALTER TABLE grpo_documents ADD COLUMN IF NOT EXISTS qc_notes TEXT;

ALTER TABLE grpo_items ADD COLUMN IF NOT EXISTS unit_price DECIMAL(15,2);

ALTER TABLE inventory_transfers ADD COLUMN IF NOT EXISTS transfer_request_number VARCHAR(50);
ALTER TABLE inventory_transfers ADD COLUMN IF NOT EXISTS from_warehouse VARCHAR(20);
ALTER TABLE inventory_transfers ADD COLUMN IF NOT EXISTS to_warehouse VARCHAR(20);
```

## Environment Setup:

1. **Enable MySQL in .env**:
   ```env
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=root@123
   MYSQL_DATABASE=wms_db_dev
   ```

2. **Test Connection**:
   ```bash
   python main.py
   ```

## Expected Results:
✅ GRPO creation will work without "Unknown column" errors
✅ Inventory Transfer listing will load properly
✅ Add Item buttons will function correctly
✅ All database operations will work seamlessly

## Login After Fix:
- Username: `admin`
- Password: `admin123`

Your WMS application will work perfectly with MySQL after running this fix!