# URGENT: Fix MySQL Database Column Error

## The Issue
Your application is crashing because your MySQL database is missing the `qc_status` column in the `inventory_transfer_items` table.

## Quick Fix (Choose One Method)

### Method 1: Direct SQL Commands
Open your MySQL command line or phpMyAdmin and run these commands:

```sql
-- Connect to your database first
USE wms_database;

-- Add missing column to inventory_transfer_items table
ALTER TABLE inventory_transfer_items 
ADD COLUMN qc_status VARCHAR(20) DEFAULT 'pending';

-- Add missing columns to inventory_transfers table
ALTER TABLE inventory_transfers 
ADD COLUMN qc_approver_id INT,
ADD COLUMN qc_approved_at DATETIME,
ADD COLUMN qc_notes TEXT;

-- Add foreign key constraint
ALTER TABLE inventory_transfers 
ADD CONSTRAINT fk_inventory_transfers_qc_approver 
FOREIGN KEY (qc_approver_id) REFERENCES users(id);
```

### Method 2: Run the Migration Script
```bash
python mysql_inventory_transfer_migration.py
```

### Method 3: MySQL Workbench
1. Open MySQL Workbench
2. Connect to your database
3. Copy and paste the SQL commands from Method 1
4. Execute them

## Verify the Fix
After running the commands, check that the columns exist:

```sql
DESCRIBE inventory_transfer_items;
DESCRIBE inventory_transfers;
```

You should see:
- `qc_status` column in `inventory_transfer_items`
- `qc_approver_id`, `qc_approved_at`, `qc_notes` columns in `inventory_transfers`

## After the Fix
1. Restart your Flask application
2. Try accessing the inventory transfer screen again
3. The error should be resolved

The application will work immediately after adding these columns to your MySQL database.