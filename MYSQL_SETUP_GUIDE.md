# MySQL Setup Guide for WMS System

## Quick Setup

Run the single migration script to set up everything:

```bash
python mysql_complete_migration.py
```

This script will:
1. Create a `.env` file with MySQL configuration
2. Create the MySQL database
3. Create all required tables with complete schema
4. Set up default admin user and branch

## What You Need

- MySQL Server installed and running
- Python with mysql-connector-python package

## Default Credentials

After setup, you can login with:
- **Username:** admin
- **Password:** admin123

## Tables Created

The migration creates these tables:
- `users` - User accounts and permissions
- `grpo_documents` - Goods Receipt PO documents
- `grpo_items` - Individual items in GRPO
- `inventory_transfers` - Inventory transfer requests
- `inventory_transfer_items` - Items in transfers
- `pick_lists` - Pick list documents
- `pick_list_items` - Items to pick
- `inventory_counts` - Inventory counting tasks
- `inventory_count_items` - Counted items
- `barcode_labels` - Generated barcode labels
- `bin_locations` - Warehouse bin locations
- `bin_items` - Items stored in bins
- `bin_scanning_logs` - Bin scanning activity logs
- `branches` - Branch/location information

## Database Configuration

The script creates a `.env` file with these settings:
- MySQL connection details
- SAP B1 integration settings (optional)
- Session configuration
- Flask application settings

## Troubleshooting

If you encounter issues:
1. Make sure MySQL server is running
2. Verify your MySQL credentials
3. Check that the database user has CREATE privileges
4. Ensure mysql-connector-python is installed: `pip install mysql-connector-python`

## Next Steps

1. Start the Flask application: `python main.py`
2. Open http://localhost:5000 in your browser
3. Login with admin/admin123
4. Configure SAP B1 settings if needed