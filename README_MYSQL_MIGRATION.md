# MySQL Migration Guide for WMS

## Overview
This guide helps you set up and migrate your MySQL database for the WMS (Warehouse Management System) application.

## Quick Fix (Single File Migration)

### Step 1: Set MySQL Environment Variables
```bash
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=wms_db_dev
```

Or create a `.env` file with:
```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=wms_db_dev
```

### Step 2: Run the Complete Migration
```bash
python mysql_complete_migration.py
```

Or use the helper script:
```bash
python run_mysql_migration.py
```

## What the Migration Does

The `mysql_complete_migration.py` script will:

### ✅ Fix Missing Columns in inventory_transfer_items
- `qc_status` (VARCHAR(20)) - Quality control status (pending/approved/rejected)
- `qc_notes` (TEXT) - Quality control notes
- `serial_number` (VARCHAR(50)) - Item serial number
- `expiry_date` (DATE) - Item expiry date
- `manufacture_date` (DATE) - Item manufacture date
- `unit_price` (DECIMAL(15,4)) - Unit price
- `total_value` (DECIMAL(15,2)) - Total value
- `from_warehouse_code` (VARCHAR(10)) - From warehouse code
- `to_warehouse_code` (VARCHAR(10)) - To warehouse code
- `base_entry` (INT) - SAP base entry reference
- `base_line` (INT) - SAP base line reference
- `sap_line_number` (INT) - SAP line number
- `updated_at` (DATETIME) - Last update timestamp

### ✅ Fix Missing Columns in inventory_transfers
- `transfer_request_number` (VARCHAR(50)) - Transfer request number
- `from_warehouse` (VARCHAR(20)) - Source warehouse
- `to_warehouse` (VARCHAR(20)) - Destination warehouse
- `transfer_type` (VARCHAR(20)) - Transfer type (warehouse/bin/emergency)
- `priority` (VARCHAR(10)) - Transfer priority (low/normal/high/urgent)
- `reason_code` (VARCHAR(20)) - Reason code for transfer
- `notes` (TEXT) - Transfer notes
- `qc_approver_id` (INT) - QC approver user ID
- `qc_approved_at` (DATETIME) - QC approval timestamp
- `qc_notes` (TEXT) - QC approval notes

### ✅ Fix Missing Columns in grpo_documents
- `po_date` (DATE) - Purchase order date
- `po_total` (DECIMAL(15,2)) - Purchase order total
- `qc_notes` (TEXT) - QC notes
- `notes` (TEXT) - General notes
- `branch_id` (VARCHAR(10)) - Branch ID
- `reference_number` (VARCHAR(50)) - Reference number
- `vendor_code` (VARCHAR(50)) - Vendor code
- `vendor_name` (VARCHAR(200)) - Vendor name
- `delivery_note_number` (VARCHAR(50)) - Delivery note number
- `invoice_number` (VARCHAR(50)) - Invoice number
- `currency` (VARCHAR(3)) - Currency code

### ✅ Fix Missing Columns in grpo_items
- `serial_number` (VARCHAR(50)) - Serial number
- `expiry_date` (DATE) - Expiry date
- `manufacture_date` (DATE) - Manufacture date
- `unit_price` (DECIMAL(15,4)) - Unit price
- `line_total` (DECIMAL(15,2)) - Line total
- `tax_rate` (DECIMAL(5,2)) - Tax rate
- `tax_amount` (DECIMAL(15,2)) - Tax amount
- `discount_percent` (DECIMAL(5,2)) - Discount percentage
- `discount_amount` (DECIMAL(15,2)) - Discount amount
- `qc_notes` (TEXT) - QC notes
- `barcode` (VARCHAR(100)) - Barcode

### ✅ Fix Missing Columns in users
- `first_name` (VARCHAR(50)) - First name
- `last_name` (VARCHAR(50)) - Last name
- `role` (VARCHAR(20)) - User role
- `is_active` (BOOLEAN) - Active status
- `branch_id` (VARCHAR(10)) - Branch ID
- `default_branch_id` (VARCHAR(10)) - Default branch ID
- `phone` (VARCHAR(20)) - Phone number
- `created_at` (DATETIME) - Creation timestamp
- `updated_at` (DATETIME) - Update timestamp
- `last_login` (DATETIME) - Last login timestamp
- `failed_login_attempts` (INT) - Failed login attempts
- `locked_until` (DATETIME) - Account lock until

### ✅ Create Missing Tables
- `branches` - Branch management
- `user_sessions` - User session tracking

### ✅ Create Performance Indexes
- Indexes for all major tables to improve query performance

## Error Resolution

### Error: "Unknown column 'qc_status' in 'field list'"
This error occurs when the `inventory_transfer_items` table is missing the `qc_status` column.

**Solution:** Run the migration script:
```bash
python mysql_complete_migration.py
```

### Error: "Can't connect to MySQL server"
This error occurs when MySQL environment variables are not set correctly.

**Solution:** 
1. Set environment variables correctly
2. Ensure MySQL server is running
3. Check username/password credentials

### Error: "Access denied for user"
This error occurs when MySQL credentials are incorrect.

**Solution:** 
1. Check username and password
2. Ensure user has CREATE/ALTER permissions
3. Create the database if it doesn't exist

## After Migration

After successful migration:
1. Restart your WMS application
2. The application should connect to MySQL successfully
3. All inventory transfer functionality should work properly

## Troubleshooting

If you encounter issues:
1. Check MySQL server is running
2. Verify environment variables are set correctly
3. Ensure user has proper database permissions
4. Check the application logs for specific error messages

## Support Files Created

- `mysql_complete_migration.py` - Complete migration script
- `run_mysql_migration.py` - Helper script to run migration
- This README file for documentation

For additional help, check the application logs or contact support.