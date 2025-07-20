# 🚨 Inventory Transfer & GRPO MySQL Database Fix

## Issues Identified:
Your MySQL database is missing these critical columns:

### GRPO Documents Table Missing:
- `po_date` (DATETIME) 
- `po_total` (DECIMAL)
- `qc_notes` (TEXT)

### GRPO Items Table Missing:
- `unit_price` (DECIMAL)

### Inventory Transfers Table Missing:
- `transfer_request_number` (VARCHAR)
- `from_warehouse` (VARCHAR)
- `to_warehouse` (VARCHAR)

## ✅ COMPLETE FIX SOLUTION:

### For Local Development (Your Machine):

1. **Run the Database Fix Script**:
   ```bash
   python quick_mysql_fix.py
   ```

2. **Enable MySQL in .env file**:
   ```env
   # Uncomment these lines in your local .env file:
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=root@123
   MYSQL_DATABASE=wms_db_dev
   ```

3. **Alternative Manual Fix** (if script fails):
   ```sql
   USE wms_db_dev;
   
   -- Fix GRPO Documents
   ALTER TABLE grpo_documents ADD COLUMN po_date DATETIME;
   ALTER TABLE grpo_documents ADD COLUMN po_total DECIMAL(15,2);
   ALTER TABLE grpo_documents ADD COLUMN qc_notes TEXT;
   
   -- Fix GRPO Items
   ALTER TABLE grpo_items ADD COLUMN unit_price DECIMAL(15,2);
   
   -- Fix Inventory Transfers  
   ALTER TABLE inventory_transfers ADD COLUMN transfer_request_number VARCHAR(50);
   ALTER TABLE inventory_transfers ADD COLUMN from_warehouse VARCHAR(20);
   ALTER TABLE inventory_transfers ADD COLUMN to_warehouse VARCHAR(20);
   ```

### For Replit (Production):
No action needed - PostgreSQL database already has correct schema.

## What Each Fix Resolves:

1. **GRPO Creation Error**: "Unknown column 'po_date'" → Fixed
2. **Inventory Transfer List Error**: "Unknown column 'transfer_request_number'" → Fixed
3. **GRPO Add Item Button**: Will work properly after schema fix
4. **Inventory Transfer Edit Data**: Will load actual data instead of samples

## Test After Fix:
1. Login: username=`admin`, password=`admin123`
2. Create GRPO with PO number (should work without errors)
3. Access Inventory Transfer module (should load properly)
4. Test Add Item buttons in GRPO (should function correctly)

## Database Priority:
- **Local Development**: MySQL (after running fix)
- **Replit Production**: PostgreSQL (already working)

Your application supports both databases seamlessly!