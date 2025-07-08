# Local Development Setup

This guide will help you set up the WMS application for local development.

## Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_local.py
   ```

2. **Start the application:**
   ```bash
   python main.py
   ```

3. **Access the application:**
   - Open your browser and go to `http://localhost:5000`
   - Login with username: `admin` and password: `admin123`

## Manual Setup

If you prefer to set up manually:

### 1. Install Dependencies

```bash
pip install flask flask-sqlalchemy flask-login werkzeug sqlalchemy psycopg2-binary requests gunicorn
```

### 2. Create Required Directories

```bash
mkdir -p instance static templates logs
```

### 3. Environment Variables

Create a `.env` file (optional for local development):

```env
SESSION_SECRET=your-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Database Configuration

For local development, the application will automatically use SQLite database stored in:
- `instance/wms.db` (preferred)
- Or temp directory if instance directory is not writable

### 5. Run the Application

```bash
python main.py
```

## Troubleshooting

### Database Issues

If you encounter database-related errors:

1. **Permission Issues**: The application will try to create the database in the `instance` directory. If this fails, it will use the system temp directory.

2. **SQLite Path Issues**: Make sure the current directory is writable, or the application will fallback to using the temp directory.

3. **Missing Tables**: The application automatically creates all required tables on startup.

### Common Solutions

1. **Run as Administrator** (Windows) or with `sudo` (Linux/Mac) if you encounter permission issues.

2. **Check Python Version**: Ensure you're using Python 3.8 or higher.

3. **Virtual Environment**: Consider using a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

## Default Login

- **Username**: `admin`
- **Password**: `admin123`

## Features Available in Local Mode

- ✅ User authentication
- ✅ Basic navigation
- ✅ GRPO (Goods Receipt) functionality
- ✅ Inventory management
- ✅ Pick lists
- ✅ Barcode operations
- ❌ SAP B1 integration (requires server configuration)

## SAP B1 Integration

To enable SAP B1 integration in local development:

1. Set the following environment variables in your `.env` file:
   ```env
   SAP_B1_SERVER=https://your-sap-server:50000
   SAP_B1_USERNAME=your-username
   SAP_B1_PASSWORD=your-password
   SAP_B1_COMPANY_DB=your-company-db
   ```

2. Ensure your SAP B1 server is accessible from your local machine.

## Production Deployment

For production deployment on Replit:
- The application automatically uses PostgreSQL
- Environment variables are configured through Replit's secrets
- No additional setup required