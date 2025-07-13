# Warehouse Management System (WMS) - SAP B1 Integration

## Overview

This is a comprehensive Warehouse Management System (WMS) built with Flask that integrates with SAP Business One (B1) for enterprise-level warehouse operations. The system is designed as a Progressive Web App (PWA) optimized for handheld devices and barcode scanning operations.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL (configured via environment variables)
- **Authentication**: Flask-Login for user session management
- **SAP Integration**: Custom SAP B1 Service Layer integration via REST API
- **Security**: Password hashing with Werkzeug security utilities

### Frontend Architecture
- **UI Framework**: Bootstrap 5 for responsive design
- **PWA Features**: Service worker, manifest.json, offline capabilities
- **Barcode Scanning**: QuaggaJS and QR Scanner libraries
- **Icons**: Feather Icons for consistent UI elements
- **JavaScript**: Vanilla JS with class-based architecture

### Database Schema
- **Users**: Role-based access control (admin, manager, user, qc)
- **GRPO Documents**: Goods Receipt against Purchase Orders
- **Inventory Management**: Transfers, pick lists, counting tasks
- **Barcode Labels**: Label generation and reprinting functionality

## Key Components

### 1. Authentication System
- User login with username/password
- Role-based permissions
- Branch-specific access control
- Session management with Flask-Login

### 2. SAP B1 Integration
- **Service Layer Connection**: REST API communication
- **Authentication**: Session-based login to SAP B1
- **Data Synchronization**: Real-time integration for POs, inventory, and documents
- **Error Handling**: Comprehensive logging and error management

### 3. Warehouse Operations
- **GRPO (Goods Receipt PO)**: Scan PO numbers, validate items, record receipts
- **Inventory Transfer**: Inter-warehouse and bin-to-bin transfers
- **Pick Lists**: Sales order-based picking operations
- **Inventory Counting**: Cycle counting and physical inventory tasks
- **Bin Scanning**: Display all items in a specific bin location

### 4. Barcode Management
- **Label Generation**: Multiple formats (standard, large, small, custom)
- **Barcode Scanning**: Support for multiple barcode types
- **QR Code Generation**: For items without supplier barcodes
- **Label Reprinting**: Search and reprint existing labels

### 5. Progressive Web App Features
- **Offline Capability**: Service worker for caching
- **Mobile Optimization**: Responsive design for handheld devices
- **App-like Experience**: Manifest for mobile installation
- **Camera Integration**: Barcode scanning through device camera

## Data Flow

1. **User Authentication**: Login → Role validation → Branch assignment
2. **SAP Integration**: Connect to SAP B1 → Authenticate → Fetch data
3. **Warehouse Operations**: Scan/Select → Validate → Process → Update SAP
4. **Barcode Operations**: Generate → Print → Scan → Validate → Update inventory

## External Dependencies

### SAP B1 Integration
- **Service Layer URL**: Configured via SAP_B1_SERVER environment variable
- **Authentication**: Username/password for SAP B1 login
- **Company Database**: Specific SAP B1 company database connection

### Third-Party Libraries
- **Bootstrap 5**: UI framework
- **QuaggaJS**: Barcode scanning library
- **QR Scanner**: QR code scanning functionality
- **Feather Icons**: Icon library
- **jQuery**: JavaScript utilities

### Environment Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Flask session encryption key
- `SAP_B1_SERVER`: SAP B1 Service Layer endpoint
- `SAP_B1_USERNAME`: SAP B1 user credentials
- `SAP_B1_PASSWORD`: SAP B1 user password
- `SAP_B1_COMPANY_DB`: SAP B1 company database name

## Deployment Strategy

### Development Environment
- Flask development server with debug mode
- SQLAlchemy database auto-creation
- Environment variables for configuration
- Hot reload for development

### Production Considerations
- WSGI server deployment (Gunicorn recommended)
- PostgreSQL database with connection pooling
- SSL/TLS for SAP B1 communication
- Service worker caching for offline functionality
- Mobile device optimization

### Security Measures
- Password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection (setup in JavaScript)
- Role-based access control
- Environment-based configuration

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Migration completed from Replit Agent to Replit environment:
  - Added PostgreSQL database with proper environment variables
  - Fixed missing template files (grpo_detail.html, inventory_transfer_detail.html)
  - Updated SAP integration to handle offline mode gracefully
  - Resolved database schema issues by enforcing PostgreSQL usage
  - Removed SQLite fallback to prevent schema conflicts
  - Application now runs without errors on Replit with full GRPO functionality
- July 08, 2025. Enhanced Database Support:
  - Added MS SQL Server support for local development
  - Created comprehensive database setup scripts
  - Added environment configuration examples
  - Improved database connection handling with proper fallbacks
  - Added pyodbc dependency for SQL Server connectivity
- July 08, 2025. Comprehensive SAP B1 Integration Enhancement:
  - Implemented complete SAP master data synchronization (warehouses, bins, business partners)
  - Added automated GRPO approval-to-posting workflow with draft/post options
  - Enhanced bin location synchronization with real-time SAP data
  - Added manual posting capability for approved GRPOs
  - Integrated SAP data sync button in admin dashboard
  - Improved error handling with offline mode graceful fallback
- July 08, 2025. Migration from Replit Agent to Replit Environment Complete:
  - Successfully migrated project from Replit Agent to standard Replit environment
  - Fixed PostgreSQL database configuration for Replit deployment
  - Enhanced local development support with SQLite fallback and proper path handling
  - Created comprehensive local setup scripts (setup_local.py and README_LOCAL_SETUP.md)
  - Added robust database connection handling for both Replit and local environments
  - Installed all required dependencies including gunicorn for production deployment
  - Fixed missing model imports to ensure all database tables are created properly
  - Application now runs seamlessly in both Replit and local development environments
- July 08, 2025. Final Migration to Replit Environment:
  - Successfully migrated from Replit Agent to Replit environment
  - Fixed database configuration to work both in Replit (PostgreSQL) and locally (SQLite)
  - Installed missing gunicorn dependency for production deployment
  - Fixed missing database models by importing models_extensions
  - Created default branch and admin user for initial setup
  - Application now runs successfully on Replit with proper database initialization
- July 11, 2025. Enhanced Purchase Delivery Note Integration:
  - Implemented Purchase Delivery Note creation in SAP B1 for PO closure
  - Added enhanced GRPO item editing functionality with received quantity focus
  - Fixed PostgreSQL database connection and data storage issues
  - Updated SAP integration to create Purchase Delivery Notes with BaseType 22 referencing
  - Added comprehensive edit functionality for GRPO line items
  - Enhanced QC approval workflow to post Purchase Delivery Notes to SAP B1
- July 11, 2025. Enhanced SAP B1 Integration and GRPO Functionality:
  - Implemented Purchase Delivery Note creation for closing POs in SAP B1
  - Enhanced GRPO approval workflow with Purchase Delivery Note posting
  - Added GRPO line item edit functionality for received quantities
  - Created comprehensive edit interface for GRPO items with validation
  - Configured PostgreSQL database for production deployment
  - Fixed database storage issues and improved data persistence
  - Added support for BaseType 22 (Purchase Order) reference in delivery notes
  - Implemented proper warehouse code extraction from bin locations
- July 12, 2025. Comprehensive Issue Resolution:
  - Fixed bin code retrieval to use 'Warehouse' field instead of 'WarehouseCode' for proper filtering
  - Enhanced barcode generation with proper WMS format (WMS-ITEMCODE-RANDOMHEX)
  - Implemented automatic barcode generation for GRPO line items
  - Added smart duplicate prevention for PO line items (shows "Fully Received" only when complete quantity received)
  - Created warehouse selection interface for inventory transfers
  - Fixed MSSQL integration issues with proper connection handling
  - Enhanced inline editing functionality for received quantity, batch number, and expiration date
  - Implemented real-time field updates without page refresh
  - Added comprehensive error handling and user feedback
  - Fixed partial receipt logic to allow multiple receipts until PO line is fully received
- July 12, 2025. Migration to Replit Environment Complete:
  - Successfully migrated from Replit Agent to Replit environment
  - Fixed GRPO fully received logic: Now correctly checks received quantity against open quantity
  - Enhanced Purchase Delivery Note creation with proper SAP B1 field mapping
  - Improved QC approval workflow to only include approved items in Purchase Delivery Notes
  - Added comprehensive error handling and logging for SAP B1 integration
  - Implemented proper BaseType 22 (Purchase Order) referencing in delivery notes
  - Enhanced batch and bin location mapping for inventory accuracy
  - Added proper reference fields (GRPO ID, PO number) for audit trail
- July 13, 2025. Enhanced GRPO Creation and MSSQL Database Support:
  - Added PO line status validation: Only allows GRPO creation for POs with "bost_Open" status
  - Implemented duplicate GRPO prevention: Checks for existing GRPO before creating new one
  - Added MSSQL database connection support with proper environment variable configuration
  - Enhanced GRPO detail template to display PO line status (Open/Closed) and open quantities
  - Created MSSQL setup script (setup_mssql_env.py) for easy database configuration
  - Improved database connection priority: MSSQL > PostgreSQL > SQLite fallback
  - Added comprehensive validation for PO open quantities before allowing item additions
- July 13, 2025. Final Migration to Replit Environment Complete:
  - Successfully migrated WMS application from Replit Agent to Replit environment
  - Configured PostgreSQL database for production deployment on Replit
  - Maintained backward compatibility with local MSSQL and SQLite configurations
  - Application now runs seamlessly on Replit with gunicorn production server
  - All dependencies properly installed and configured for Replit deployment
  - Database fallback system ensures compatibility across all environments
  - Ready for production deployment on Replit platform
- July 13, 2025. Fixed PO Line Status Validation Issue:
  - Resolved "Line Status not Open" error when validating PO numbers in offline mode
  - Added LineStatus: 'bost_Open' to mock data in SAP integration for offline testing
  - Enhanced validation logic to handle missing LineStatus fields gracefully
  - Added debug logging for PO validation troubleshooting
  - Improved offline mode compatibility for local development environments
- July 13, 2025. Enhanced Local SQL Server Support:
  - Added comprehensive SQL Server connection configurations for various environments
  - Created local SQL Server diagnostic and fix scripts
  - Enhanced MSSQL connection handling with multiple driver fallbacks
  - Added support for SQL Server Management Studio 20.2.30.0 environment
  - Improved connection timeout and error handling for local development
- July 13, 2025. Complete MySQL Database Integration:
  - Added MySQL as primary database option for local development
  - Installed PyMySQL and MySQL Connector drivers with proper fallback mechanisms
  - Enhanced database detection logic to handle MySQL-specific SQL syntax
  - Fixed database-specific queries (NOW() vs CURRENT_TIMESTAMP, ON DUPLICATE KEY UPDATE vs ON CONFLICT)
  - Created comprehensive MySQL setup scripts (setup_mysql_env.py, install_mysql_local.py)
  - Updated database connection priority: MySQL → MSSQL → PostgreSQL → SQLite
  - Resolved PO line status validation issue by enhancing database compatibility
  - Added MySQL-specific table creation and upsert syntax for bin locations and warehouses
- July 13, 2025. Enhanced Purchase Delivery Note Integration with Exact SAP B1 Specifications:
  - Implemented comprehensive Purchase Delivery Note creation with exact JSON structure
  - Added automatic external reference number generation (EXT-REF-YYYYMMDD-XXX format)
  - Created BusinessPlaceID lookup functionality from warehouse codes via SAP B1 API
  - Enhanced batch number mapping with complete field structure (ManufacturerSerialNumber, InternalSerialNumber, ExpiryDate)
  - Added proper BaseType 22 (Purchase Order) referencing with BaseEntry and BaseLine mapping
  - Implemented sequence table for unique reference number generation per day
  - Enhanced error handling and logging for Purchase Delivery Note creation process
  - Added comprehensive field mapping: CardCode, DocDate, DocDueDate, Comments, NumAtCard, BPL_IDAssignedToInvoice
  - Created complete document line structure with proper quantity and warehouse code extraction
- July 13, 2025. Database Schema Migration and Enhanced Barcode Functionality:
  - Fixed missing 'notes' attribute in GRPODocument model with PostgreSQL database migration
  - Enhanced JSON logging for SAP API calls with detailed formatting for debugging
  - Implemented complete barcode generation and printing API endpoints
  - Added functional JavaScript integration for barcode generation and printing in GRPO templates
  - Created MySQL-compatible database migration script (migrate_database_mysql.py)
  - Fixed warehouse code display issues in GRPO screens
  - Resolved duplicate route definitions and application startup errors
  - Enhanced WMS barcode format: WMS-ITEMCODE-RANDOMHEX with proper database tracking
- July 13, 2025. UI/UX Enhancement and JSON Debugging Features:
  - Replaced bin location dropdown with warehouse code input field for simplified data entry
  - Added "Preview JSON" button to show exact Purchase Delivery Note structure before SAP B1 posting
  - Implemented JSON preview modal with copy-to-clipboard functionality for debugging
  - Enhanced warehouse code display in GRPO item listings for better visibility
  - Updated add item form to use warehouse code instead of complex bin location selection
  - Created comprehensive JSON preview API endpoint for real-time SAP B1 payload inspection