from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False,
                  default='user')  # admin, manager, user, qc
    branch_id = db.Column(db.String(10), nullable=True)
    branch_name = db.Column(db.String(100), nullable=True)
    default_branch_id = db.Column(
        db.String(10), nullable=True)  # Default branch if none selected
    user_is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(
        db.Boolean, default=False)  # Force password change on next login
    last_login = db.Column(db.DateTime, nullable=True)
    permissions = db.Column(db.Text,
                         nullable=True)  # JSON string of screen permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    def get_permissions(self):
        """Get user permissions as a dictionary"""
        import json
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except:
                return {}
        return self.get_default_permissions()

    def set_permissions(self, perms_dict):
        """Set user permissions from a dictionary"""
        import json
        self.permissions = json.dumps(perms_dict)

    def get_default_permissions(self):
        """Get default permissions based on role"""
        permissions = {
            'dashboard': True,
            'grpo': False,
            'inventory_transfer': False,
            'pick_list': False,
            'inventory_counting': False,
            'bin_scanning': False,
            'label_printing': False,
            'user_management': False,
            'qc_dashboard': False
        }

        if self.role == 'admin':
            # Admin has access to everything
            for key in permissions:
                permissions[key] = True
        elif self.role == 'manager':
            permissions.update({
                'grpo': True,
                'inventory_transfer': True,
                'pick_list': True,
                'inventory_counting': True,
                'bin_scanning': True,
                'label_printing': True,
                'user_management': True
            })
        elif self.role == 'qc':
            permissions.update({
                'grpo': True,
                'qc_dashboard': True,
                'bin_scanning': True
            })
        elif self.role == 'user':
            permissions.update({
                'grpo': True,
                'inventory_transfer': True,
                'pick_list': True,
                'inventory_counting': True,
                'bin_scanning': True,
                'label_printing': True
            })

        return permissions

    def has_permission(self, screen):
        """Check if user has permission for a specific screen"""
        if self.role == 'admin':
            return True
        return self.get_permissions().get(screen, False)

    # Relationships
    grpo_documents = relationship('GRPODocument',
                                  back_populates='user',
                                  foreign_keys='GRPODocument.user_id')
    inventory_transfers = relationship('InventoryTransfer',
                                       back_populates='user',
                                       foreign_keys='InventoryTransfer.user_id')
    pick_lists = relationship('PickList',
                              back_populates='user',
                              foreign_keys='PickList.user_id')
    inventory_counts = relationship('InventoryCount', back_populates='user')


class GRPODocument(db.Model):
    __tablename__ = 'grpo_documents'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(20), nullable=False)
    sap_document_number = db.Column(db.String(20), nullable=True)
    supplier_code = db.Column(db.String(50), nullable=True)  # CardCode from SAP
    supplier_name = db.Column(db.String(200), nullable=True)
    po_date = db.Column(db.DateTime, nullable=True)
    po_total = db.Column(db.Float, nullable=True)
    status = db.Column(
        db.String(20),
        default='draft')  # draft, submitted, approved, posted, rejected
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qc_user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=True)  # QC approver
    qc_notes = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # General notes/comments for the GRPO
    draft_or_post = db.Column(db.String(10), default='draft')  # draft, post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User',
                        back_populates='grpo_documents',
                        foreign_keys=[user_id])
    qc_user = relationship('User', foreign_keys=[qc_user_id])
    items = relationship('GRPOItem', back_populates='grpo_document')


class GRPOItem(db.Model):
    __tablename__ = 'grpo_items'

    id = db.Column(db.Integer, primary_key=True)
    grpo_document_id = db.Column(db.Integer,
                              db.ForeignKey('grpo_documents.id'),
                              nullable=False)
    po_line_number = db.Column(db.Integer, nullable=True)  # Line number from PO
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    po_quantity = db.Column(db.Float, nullable=True)  # Original PO quantity
    open_quantity = db.Column(db.Float, nullable=True)  # Remaining open quantity
    received_quantity = db.Column(db.Float,
                               nullable=False)  # Quantity being received
    unit_of_measure = db.Column(db.String(10), nullable=False)
    unit_price = db.Column(db.Float, nullable=True)
    bin_location = db.Column(db.String(20), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    serial_number = db.Column(db.String(50), nullable=True)  # Serial number for serial-managed items
    expiration_date = db.Column(db.DateTime, nullable=True)
    supplier_barcode = db.Column(db.String(100),
                              nullable=True)  # Original supplier barcode
    generated_barcode = db.Column(db.String(100),
                               nullable=True)  # WMS generated barcode
    barcode_printed = db.Column(db.Boolean, default=False)
    qc_status = db.Column(db.String(20),
                       default='pending')  # pending, approved, rejected
    qc_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grpo_document = relationship('GRPODocument', back_populates='items')


class InventoryTransfer(db.Model):
    __tablename__ = 'inventory_transfers'

    id = db.Column(db.Integer, primary_key=True)
    transfer_request_number = db.Column(db.String(20), nullable=False)
    sap_document_number = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20),
                    default='draft')  # draft, submitted, qc_approved, posted, rejected
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qc_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    qc_approved_at = db.Column(db.DateTime, nullable=True)
    qc_notes = db.Column(db.Text, nullable=True)
    from_warehouse = db.Column(db.String(20), nullable=True)
    to_warehouse = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='inventory_transfers', foreign_keys=[user_id])
    qc_approver = relationship('User', foreign_keys=[qc_approver_id])
    items = relationship('InventoryTransferItem',
                         back_populates='inventory_transfer')


class InventoryTransferItem(db.Model):
    __tablename__ = 'inventory_transfer_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_transfer_id = db.Column(db.Integer,
                                   db.ForeignKey('inventory_transfers.id'),
                                   nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    requested_quantity = db.Column(db.Float, nullable=False)  # Original requested quantity
    transferred_quantity = db.Column(db.Float, default=0)  # Actually transferred quantity
    remaining_quantity = db.Column(db.Float, nullable=False)  # Remaining to transfer
    unit_of_measure = db.Column(db.String(10), nullable=False)
    from_bin = db.Column(db.String(20), nullable=False)
    to_bin = db.Column(db.String(20), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    available_batches = db.Column(db.Text, nullable=True)  # JSON list of available batches
    qc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    qc_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inventory_transfer = relationship('InventoryTransfer',
                                      back_populates='items')


class PickList(db.Model):
    __tablename__ = 'pick_lists'

    id = db.Column(db.Integer, primary_key=True)
    sales_order_number = db.Column(db.String(20), nullable=False)
    pick_list_number = db.Column(db.String(20), nullable=False)
    status = db.Column(
        db.String(20),
        default='pending')  # pending, approved, rejected, completed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User',
                        back_populates='pick_lists',
                        foreign_keys=[user_id])
    approver = relationship('User', foreign_keys=[approver_id])
    items = relationship('PickListItem', back_populates='pick_list')


class PickListItem(db.Model):
    __tablename__ = 'pick_list_items'

    id = db.Column(db.Integer, primary_key=True)
    pick_list_id = db.Column(db.Integer, db.ForeignKey('pick_lists.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    picked_quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(10), nullable=False)
    bin_location = db.Column(db.String(20), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pick_list = relationship('PickList', back_populates='items')


class InventoryCount(db.Model):
    __tablename__ = 'inventory_counts'

    id = db.Column(db.Integer, primary_key=True)
    count_number = db.Column(db.String(20), nullable=False)
    warehouse_code = db.Column(db.String(10), nullable=False)
    bin_location = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20),
                    default='assigned')  # assigned, in_progress, completed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='inventory_counts')
    items = relationship('InventoryCountItem',
                         back_populates='inventory_count')


class InventoryCountItem(db.Model):
    __tablename__ = 'inventory_count_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_count_id = db.Column(db.Integer,
                                db.ForeignKey('inventory_counts.id'),
                                nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    system_quantity = db.Column(db.Float, nullable=False)
    counted_quantity = db.Column(db.Float, nullable=False)
    variance = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(10), nullable=False)
    batch_number = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inventory_count = relationship('InventoryCount', back_populates='items')


class BarcodeLabel(db.Model):
    __tablename__ = 'barcode_labels'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), nullable=False)
    barcode = db.Column(db.String(100), nullable=False)
    label_format = db.Column(db.String(20), nullable=False)
    print_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_printed = db.Column(db.DateTime, nullable=True)
