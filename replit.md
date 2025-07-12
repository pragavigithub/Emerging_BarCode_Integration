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