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