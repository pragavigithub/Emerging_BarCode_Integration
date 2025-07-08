# Local Development Setup Guide

## Database Setup Options

### Option 1: MS SQL Server (Recommended for Production-like Environment)

1. **Install SQL Server** (if not already installed)
   - Download SQL Server Express from Microsoft
   - Install with default settings

2. **Create Database**
   ```sql
   CREATE DATABASE WMS_DB;
   ```

3. **Create Environment File**
   - Copy `.env.example` to `.env`
   - Update the MSSQL settings:
   ```
   MSSQL_SERVER=localhost
   MSSQL_DATABASE=WMS_DB
   MSSQL_USERNAME=your_username
   MSSQL_PASSWORD=your_password
   ```

4. **Install ODBC Driver**
   - Download and install "ODBC Driver 17 for SQL Server" from Microsoft

### Option 2: SQLite (Quick Start)

1. **No additional setup required** - just run the application
2. Database file will be created automatically in `instance/wms.db`

## Running the Application

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Default Login**
   - Username: `admin`
   - Password: `admin123`

## Features Available

### User Management
- Create unlimited users with configurable permissions
- Role-based access control (admin, manager, user, qc)
- Screen-level authorization for each module
- Branch-based login with default assignments
- Password reset functionality for administrators

### Warehouse Operations
- Goods Receipt against Purchase Orders (GRPO)
- Inventory Transfer between locations
- Pick List management for sales orders
- Inventory Counting and cycle counts
- Bin scanning and location management
- Barcode label generation and printing

### SAP Integration
- Real-time connection to SAP Business One
- Purchase Order validation and data retrieval
- Item master data synchronization
- Document posting to SAP B1
- Offline mode for when SAP is unavailable

## Troubleshooting

### Database Connection Issues
1. Verify SQL Server is running
2. Check firewall settings
3. Ensure ODBC driver is installed
4. Verify credentials in .env file

### SAP Connection Issues
1. Check SAP B1 Service Layer is running
2. Verify network connectivity to SAP server
3. Update SAP credentials in .env file
4. Application will run in offline mode if SAP is unavailable