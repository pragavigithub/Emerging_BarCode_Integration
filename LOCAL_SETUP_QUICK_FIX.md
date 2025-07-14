# Local Development Quick Fix

If you're getting the "table grpo_documents has no column named notes" error when running locally, this is because your local SQLite database needs to be updated with the latest schema changes.

## Automatic Fix (Recommended)

The application now automatically fixes missing columns when it starts. Simply restart your local application and the schema will be updated automatically.

## Manual Fix (If Needed)

If the automatic fix doesn't work, run these commands:

### For Windows (PowerShell):
```powershell
# Navigate to your project directory
cd "E:\SAP_Integ\Git Change\20250714\6\Emerging_BarCode_Integration"

# Run the schema fix
python fix_sqlite_schema.py

# Start the application
python main.py
```

### For Command Prompt:
```cmd
cd "E:\SAP_Integ\Git Change\20250714\6\Emerging_BarCode_Integration"
python fix_sqlite_schema.py
python main.py
```

## What This Fixes

The schema fix adds these missing columns:
- `notes` column to `grpo_documents` table
- `serial_number` column to `grpo_items` table

## Database Locations

The application will try to create the database in this order:
1. `instance/database.db` (preferred)
2. `instance/wms.db` 
3. Temporary directory (fallback)

## Environment Variables

For local development, make sure your `.env` file has:
```
# Leave DATABASE_URL empty for local SQLite development
# DATABASE_URL=

# Optional SAP B1 settings (for testing)
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=Ea@12345
SAP_B1_COMPANY_DB=Test_Hutchinson
SESSION_SECRET=your-secret-key-here
```

## Troubleshooting

1. **Permission Error**: Make sure you have write permissions in your project directory
2. **Database Locked**: Close any other applications that might be using the database
3. **Module Not Found**: Make sure all dependencies are installed: `pip install -r requirements.txt`

## Success Indicators

When the fix works, you should see these messages in the console:
```
✅ Added 'notes' column to grpo_documents
✅ Added 'serial_number' column to grpo_items
✅ SQLite schema migration completed
```

## Default Login

After setup, use these credentials:
- Username: `admin`
- Password: `admin123`