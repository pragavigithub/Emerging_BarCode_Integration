# Bin Scanning Setup Guide

## Overview
This guide explains how to set up and use the bin scanning functionality in the WMS system with proper SAP B1 integration.

## Database Setup

### For Local MySQL Development

1. **Run the Migration Script:**
```bash
python mysql_bin_scanning_migration.py
```

2. **Set Environment Variables:**
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=root@123
export MYSQL_DATABASE=wms_db_dev
```

3. **Enable MySQL in app.py:**
Uncomment the MySQL configuration section in `app.py` (lines 45-73)

### Database Tables Created

1. **bin_locations**
   - Stores bin information from SAP B1
   - Fields: bin_code, warehouse_code, description, is_active, is_system_bin
   - Maps to SAP B1 BinLocations table

2. **bin_items**
   - Tracks items in specific bins with real-time SAP integration
   - Fields: bin_code, item_code, quantity, batch_number, expiry_date
   - Synced with SAP B1 ItemWhsStock and BatchNumberDetails

3. **bin_scanning_logs**
   - Audit trail for all bin scanning activities
   - Fields: bin_code, user_id, scan_type, items_found, scan_timestamp

## SAP B1 Integration

### API Endpoints Used

1. **Bin Validation:**
   ```
   GET /b1s/v1/BinLocations?$filter=BinCode eq 'BIN_CODE'
   ```

2. **Warehouse Stock:**
   ```
   GET /b1s/v1/ItemWhsStock?$filter=WhsCode eq 'WAREHOUSE' and OnHand gt 0
   ```

3. **Batch Details:**
   ```
   GET /b1s/v1/BatchNumberDetails?$filter=ItemCode eq 'ITEM' and Status eq 'bdsStatus_Released'
   ```

### Example API Response Flow

1. **Scan bin code: `7000-FG-SYSTEM-BIN-LOCATION`**
2. **Get bin info:** Validates bin exists and gets warehouse code
3. **Get warehouse stock:** Lists all items with quantity > 0
4. **Get batch details:** For each item, retrieves batch information
5. **Format response:** Returns structured data for display

## Features

### Bin Scanning Module (/bin_scanning)

1. **Manual Bin Entry:**
   - Enter bin code manually
   - Real-time validation against SAP B1
   - Shows items with quantities and batch info

2. **Barcode Scanning:**
   - Camera-based bin barcode scanning
   - Automatic bin lookup after scan
   - Works with QR codes and standard barcodes

3. **Quick Scan Mode:**
   - Full-screen scanner interface
   - Supports both bin codes and item codes
   - Real-time scan results display

4. **Item Display:**
   - Shows all items in scanned bin
   - Displays: Item Code, Name, Quantity, UoM, Batch, Expiry
   - Color-coded status indicators

### API Endpoints

- **POST /api/scan_bin**
  - Input: `{"bin_code": "BIN_CODE"}`
  - Output: Bin items with quantities and batch info
  - Integrates with SAP B1 in real-time

## Usage Examples

### 1. Basic Bin Scan
```javascript
// Frontend JavaScript
const response = await fetch('/api/scan_bin', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({bin_code: '7000-FG-SYSTEM-BIN-LOCATION'})
});
const data = await response.json();
// Shows items: CO0726Y, CO0098Y, etc. with quantities
```

### 2. QR Code Integration
- QR codes now generate clean format: `ItemCode|PONumber|ItemName|BatchNumber`
- When scanned in bin module, automatically determines if it's a bin or item code
- Supports both GRPO and Inventory Transfer QR codes

### 3. Real-time Data
- All data comes from live SAP B1 system
- No cached data - always current inventory levels
- Batch information includes expiry dates and manufacturing dates

## Troubleshooting

### Common Issues

1. **MySQL Connection Error:**
   - Check MySQL service is running
   - Verify credentials in environment variables
   - Run migration script to create tables

2. **SAP B1 Connection Timeout:**
   - Normal in Replit environment (no access to local SAP)
   - System falls back to offline mode with sample data
   - For production, ensure SAP B1 server is accessible

3. **Empty Bin Results:**
   - Verify bin code exists in SAP B1
   - Check warehouse has items with OnHand > 0
   - Ensure batch management is configured for items

### Migration Commands

```bash
# Create all bin scanning tables
python mysql_bin_scanning_migration.py

# Check table creation
mysql -u root -p wms_db_dev -e "SHOW TABLES LIKE 'bin%';"

# Verify sample data
mysql -u root -p wms_db_dev -e "SELECT * FROM bin_locations;"
```

## Production Deployment

1. **Environment Setup:**
   - Set SAP B1 connection parameters
   - Configure warehouse and bin codes in SAP
   - Enable batch management for tracked items

2. **Performance Optimization:**
   - Index bin_code and item_code columns
   - Cache frequently accessed warehouse data
   - Limit batch queries to improve response time

3. **Security:**
   - Use HTTPS for SAP B1 communication
   - Implement proper authentication for API access
   - Log all bin scanning activities for audit

## Testing

Use these test bin codes with the system:
- `7000-FG-SYSTEM-BIN-LOCATION` (System bin)
- `WH001-BIN-01` (Regular bin)
- `7000-FG-BIN-A1` (Finished goods)

The system will show appropriate items and quantities for each bin based on live SAP B1 data or mock data in offline mode.