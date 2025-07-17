# Inventory Transfer Schema Fix

## Issue Description
The inventory transfer module has been enhanced with QC approval workflow, but local development databases (SQLite) may be missing the required columns.

## Error Symptoms
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: inventory_transfers.qc_approver_id
```

## Quick Fix Solutions

### Option 1: Run the Migration Script
```bash
python migrate_inventory_transfers.py
```

### Option 2: Use the Quick Fix Script
```bash
python fix_inventory_transfer_schema.py
```

### Option 3: Manual Database Reset
```bash
# Delete the existing database and let it recreate
rm instance/warehouse.db
# Restart the application - it will recreate the database with all columns
```

## What the Migration Adds

### To `inventory_transfers` table:
- `qc_approver_id` - ID of the QC approver
- `qc_approved_at` - Timestamp when QC approved
- `qc_notes` - QC approval/rejection notes
- `from_warehouse` - Source warehouse code
- `to_warehouse` - Destination warehouse code

### To `inventory_transfer_items` table:
- `qc_status` - Status of QC approval (pending/approved/rejected)
- `qc_notes` - Item-specific QC notes

## New QC Workflow

1. **Draft** - Transfer is being prepared
2. **Submitted** - Transfer submitted for QC approval
3. **QC Approved** - Transfer approved by QC and posted to SAP B1
4. **Rejected** - Transfer rejected by QC

## Features Added

### For Users:
- Submit transfers for QC approval
- Track transfer status
- View QC notes and approval history

### For QC Staff:
- QC Dashboard (`/qc_dashboard`)
- Approve/reject transfers
- Add QC notes
- Automatic posting to SAP B1 upon approval

## Database Environment Support

The application supports multiple database types:
- **Replit**: PostgreSQL (production)
- **Local**: SQLite (development)
- **Enterprise**: MySQL/SQL Server

The migration scripts handle all database types automatically.

## Troubleshooting

### If migration fails:
1. Check database file permissions
2. Ensure no other processes are using the database
3. Try the manual reset option (Option 3)

### If QC workflow doesn't work:
1. Verify user has QC permissions
2. Check database schema was updated correctly
3. Ensure SAP B1 integration is configured

## Testing the Fix

After running the migration:
1. Go to Inventory Transfer module
2. Create a new transfer
3. Submit for QC approval
4. Login as QC user and approve/reject
5. Verify SAP B1 posting (if configured)

## Support

If you continue to experience issues:
1. Check the application logs
2. Verify database schema using SQLite browser
3. Run the migration script again
4. Contact support with error details