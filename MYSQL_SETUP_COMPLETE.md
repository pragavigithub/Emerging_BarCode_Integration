# MySQL Database Setup Guide

## Quick Setup (Recommended)

### Step 1: Install MySQL Dependencies
```bash
pip install pymysql mysql-connector-python
```

### Step 2: Run MySQL Setup Script
```bash
python setup_mysql_database.py
```

The script will:
- Ask for your MySQL connection details
- Create the database if it doesn't exist
- Create all required tables with proper schema
- Add default admin user and branch
- Save configuration to .env file

### Step 3: Update Application Configuration

The script automatically creates a `.env` file with MySQL configuration. Your Flask app will automatically use MySQL when it finds the `DATABASE_URL` environment variable.

### Step 4: Restart Application
```bash
# The application will automatically detect and use MySQL
python main.py
```

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Create MySQL Database
```sql
CREATE DATABASE warehouse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Update .env File
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=warehouse_db
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/warehouse_db
```

### 3. Run Migration Script
```bash
python mysql_migration_fix.py
```

## Default Credentials

After setup:
- **Username:** admin
- **Password:** admin123
- **Note:** Change password on first login

## Troubleshooting

### Connection Issues
1. Verify MySQL is running
2. Check username/password
3. Ensure database exists
4. Check firewall settings

### Permission Issues
```sql
GRANT ALL PRIVILEGES ON warehouse_db.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### Character Set Issues
Ensure your MySQL database uses `utf8mb4` character set for proper Unicode support.

## Features Included

The MySQL setup includes all features:
- ✅ User management with role-based access
- ✅ GRPO (Goods Receipt) module
- ✅ Inventory Transfer module
- ✅ QR code generation for items
- ✅ Pick List management
- ✅ Inventory counting
- ✅ Barcode label printing
- ✅ QC approval workflows

## Environment Variables

The setup creates these environment variables:
- `MYSQL_HOST` - MySQL server host
- `MYSQL_PORT` - MySQL server port
- `MYSQL_USER` - MySQL username
- `MYSQL_PASSWORD` - MySQL password
- `MYSQL_DATABASE` - Database name
- `DATABASE_URL` - Complete SQLAlchemy connection string

## Next Steps

1. Run the setup script
2. Restart your Flask application
3. Login with admin credentials
4. Change default password
5. Create additional users as needed
6. Configure SAP B1 integration (optional)

Your warehouse management system is now ready with MySQL database!