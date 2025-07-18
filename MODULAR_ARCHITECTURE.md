# Modular Architecture Documentation

## Overview

The WMS application has been restructured into a modular architecture to improve maintainability, scalability, and organization. Each module contains its own models, routes, and templates.

## Directory Structure

```
modules/
├── __init__.py
├── main_controller.py          # Central module registration
├── shared/                     # Common components
│   ├── __init__.py
│   └── models.py              # User, Warehouse, BinLocation, BusinessPartner
├── grpo/                      # GRPO Module
│   ├── __init__.py
│   ├── models.py              # GRPODocument, GRPOItem, PurchaseDeliveryNote
│   ├── routes.py              # GRPO routes (/grpo/*)
│   └── templates/             # GRPO-specific templates
└── inventory_transfer/        # Inventory Transfer Module
    ├── __init__.py
    ├── models.py              # InventoryTransfer, InventoryTransferItem, etc.
    ├── routes.py              # Transfer routes (/inventory_transfer/*)
    └── templates/             # Transfer-specific templates
```

## Modules

### 1. Shared Module (`modules/shared/`)
**Purpose**: Common models and utilities used across all modules

**Models**:
- `User` - User authentication and authorization
- `Warehouse` - Warehouse master data
- `BinLocation` - Bin location master data
- `BusinessPartner` - Supplier/Customer master data

### 2. GRPO Module (`modules/grpo/`)
**Purpose**: Goods Receipt against Purchase Orders

**Models**:
- `GRPODocument` - Main GRPO header
- `GRPOItem` - GRPO line items
- `PurchaseDeliveryNote` - SAP B1 posting document

**Routes** (Prefix: `/grpo/`):
- `GET /grpo/` - List all GRPOs
- `GET /grpo/detail/<id>` - GRPO detail view
- `GET|POST /grpo/create` - Create new GRPO
- `POST /grpo/<id>/submit` - Submit for QC approval
- `POST /grpo/<id>/approve` - QC approve and post to SAP
- `POST /grpo/<id>/reject` - QC reject GRPO

**Status Workflow**:
`draft` → `submitted` → `qc_approved`/`rejected`

### 3. Inventory Transfer Module (`modules/inventory_transfer/`)
**Purpose**: Inventory transfers between warehouses/bins

**Models**:
- `InventoryTransfer` - Main transfer header
- `InventoryTransferItem` - Transfer line items
- `TransferStatusHistory` - Status change audit trail
- `TransferRequest` - SAP B1 transfer requests

**Routes** (Prefix: `/inventory_transfer/`):
- `GET /inventory_transfer/` - List all transfers
- `GET /inventory_transfer/detail/<id>` - Transfer detail view
- `GET|POST /inventory_transfer/create` - Create new transfer
- `POST /inventory_transfer/<id>/submit` - Submit for QC approval
- `POST /inventory_transfer/<id>/qc_approve` - QC approve and post to SAP
- `POST /inventory_transfer/<id>/qc_reject` - QC reject transfer
- `POST /inventory_transfer/<id>/reopen` - Reopen rejected transfer

**Status Workflow**:
`draft` → `submitted` → `qc_approved`/`rejected` → `draft` (reopen)

## Enhanced Features

### Status Management
- Complete audit trail with `TransferStatusHistory`
- Status validation at each step
- Reopen functionality for rejected transfers

### Permission System
- Role-based access control
- Module-specific permissions
- QC approval workflow

### Data Integrity
- Foreign key relationships
- Cascade delete for related records
- Automatic timestamp updates

## Integration

The modular system integrates with the main application through:

```python
from modules.main_controller import register_modules

# In main.py or app.py
register_modules(app)
```

## Benefits

1. **Separation of Concerns**: Each module handles specific functionality
2. **Maintainability**: Changes to one module don't affect others
3. **Scalability**: Easy to add new modules
4. **Testability**: Each module can be tested independently
5. **Reusability**: Modules can be reused in other applications

## Migration Notes

- Existing routes remain functional
- Database schema is preserved
- Templates are organized by module
- Gradual migration possible

## Future Enhancements

- Add Pick List module
- Add Inventory Counting module
- Add Barcode Labels module
- Implement API versioning
- Add module-specific middleware