from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

from app import app, db, login_manager
from models import User, GRPODocument, GRPOItem, InventoryTransfer, InventoryTransferItem, PickList, PickListItem, InventoryCount, InventoryCountItem, BarcodeLabel
from sap_integration import SAPIntegration

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        branch_id = request.form.get('branch_id')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                # Update branch if provided
                if branch_id:
                    user.branch_id = branch_id
                    db.session.commit()
                
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Account is deactivated. Please contact administrator.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get dashboard statistics
        grpo_count = GRPODocument.query.filter_by(user_id=current_user.id).count()
        transfer_count = InventoryTransfer.query.filter_by(user_id=current_user.id).count()
        pick_list_count = PickList.query.filter_by(user_id=current_user.id).count()
        count_tasks = InventoryCount.query.filter_by(user_id=current_user.id).count()
        
        stats = {
            'grpo_count': grpo_count,
            'transfer_count': transfer_count,
            'pick_list_count': pick_list_count,
            'count_tasks': count_tasks
        }
    except Exception as e:
        logging.error(f"Database error in dashboard: {e}")
        # Handle database schema mismatch gracefully
        stats = {
            'grpo_count': 0,
            'transfer_count': 0,
            'pick_list_count': 0,
            'count_tasks': 0
        }
        flash('Database needs to be updated. Please run: python migrate_database.py', 'warning')
    
    return render_template('dashboard.html', stats=stats)

@app.route('/grpo')
@login_required
def grpo():
    try:
        documents = GRPODocument.query.filter_by(user_id=current_user.id).order_by(GRPODocument.created_at.desc()).all()
    except Exception as e:
        logging.error(f"Database error in grpo: {e}")
        documents = []
        flash('Database needs to be updated. Please run: python migrate_database.py', 'warning')
    return render_template('grpo.html', documents=documents)

@app.route('/grpo/create', methods=['POST'])
@login_required
def create_grpo():
    po_number = request.form['po_number']
    
    # Check if PO exists in SAP
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if not po_data:
        flash('Purchase Order not found in SAP B1.', 'error')
        return redirect(url_for('grpo'))
    
    # Parse SAP date safely (handles both ISO format and simple date format)
    po_date = datetime.utcnow()
    if po_data.get('DocDate'):
        date_str = po_data.get('DocDate')
        try:
            # Try ISO format first (SAP B1 format: 2025-01-08T00:00:00Z)
            if 'T' in date_str:
                po_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Simple date format
                po_date = datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError) as e:
            logging.warning(f"Could not parse PO date '{date_str}': {e}")
            po_date = datetime.utcnow()

    # Create GRPO document with PO details
    grpo_doc = GRPODocument(
        po_number=po_number,
        supplier_code=po_data.get('CardCode'),
        supplier_name=po_data.get('CardName'),
        po_date=po_date,
        po_total=po_data.get('DocTotal', 0),
        user_id=current_user.id,
        draft_or_post=request.form.get('draft_or_post', 'draft')
    )
    db.session.add(grpo_doc)
    db.session.commit()
    
    flash(f'GRPO created successfully for PO {po_number}!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_doc.id))

@app.route('/grpo/<int:grpo_id>')
@login_required
def grpo_detail(grpo_id):
    try:
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
        
        # Get PO items from SAP
        sap = SAPIntegration()
        po_items = sap.get_purchase_order_items(grpo_doc.po_number)
    except Exception as e:
        logging.error(f"Database error in grpo_detail: {e}")
        flash('Database needs to be updated. Please run: python reset_database.py', 'error')
        return redirect(url_for('grpo'))
    
    return render_template('grpo_detail.html', grpo_doc=grpo_doc, po_items=po_items)

@app.route('/grpo/<int:grpo_id>/add_item', methods=['POST'])
@login_required
def add_grpo_item(grpo_id):
    try:
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    except Exception as e:
        logging.error(f"Database error in add_grpo_item: {e}")
        flash('Database needs to be updated. Please run: python reset_database.py', 'error')
        return redirect(url_for('grpo'))
    
    item_code = request.form['item_code']
    quantity = float(request.form['quantity'])
    bin_location = request.form['bin_location']
    batch_number = request.form.get('batch_number')
    
    # Get PO line item details if available
    sap = SAPIntegration()
    po_items = sap.get_purchase_order_items(grpo_doc.po_number)
    
    # Find matching PO line item
    po_line_item = None
    for po_item in po_items:
        if po_item.get('ItemCode') == item_code:
            po_line_item = po_item
            break
    
    # Generate barcode if not provided
    generated_barcode = None
    if not request.form.get('supplier_barcode'):
        import uuid
        generated_barcode = f"WMS-{item_code}-{uuid.uuid4().hex[:8].upper()}"
    
    # Create GRPO item with enhanced details
    grpo_item = GRPOItem(
        grpo_document_id=grpo_doc.id,
        po_line_number=po_line_item.get('LineNum') if po_line_item else None,
        item_code=item_code,
        item_name=request.form['item_name'],
        po_quantity=po_line_item.get('Quantity') if po_line_item else quantity,
        open_quantity=po_line_item.get('OpenQuantity') if po_line_item else quantity,
        received_quantity=quantity,
        unit_of_measure=request.form['unit_of_measure'],
        unit_price=po_line_item.get('Price') if po_line_item else 0,
        bin_location=bin_location,
        batch_number=batch_number,
        expiration_date=datetime.strptime(request.form['expiration_date'], '%Y-%m-%d') if request.form.get('expiration_date') else None,
        supplier_barcode=request.form.get('supplier_barcode'),
        generated_barcode=generated_barcode
    )
    db.session.add(grpo_item)
    db.session.commit()
    
    flash('Item added to GRPO successfully!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/submit', methods=['POST'])
@login_required
def submit_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Update status to submitted for QC approval
    grpo_doc.status = 'submitted'
    db.session.commit()
    
    flash('GRPO submitted for QC approval!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/approve', methods=['POST'])
@login_required
def approve_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Check if user has QC role
    if current_user.role not in ['qc', 'manager', 'admin']:
        flash('You do not have permission to approve GRPO documents.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    # Submit to SAP B1
    sap = SAPIntegration()
    result = sap.create_goods_receipt_po(grpo_doc)
    
    if result['success']:
        grpo_doc.status = 'approved' if grpo_doc.draft_or_post == 'draft' else 'posted'
        grpo_doc.sap_document_number = result['document_number']
        grpo_doc.qc_user_id = current_user.id
        grpo_doc.qc_notes = request.form.get('qc_notes', '')
        db.session.commit()
        
        # Update all items QC status
        for item in grpo_doc.items:
            item.qc_status = 'approved'
        db.session.commit()
        
        flash('GRPO approved and posted to SAP B1!', 'success')
    else:
        flash(f'Error posting GRPO to SAP: {result["error"]}', 'error')
    
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/reject', methods=['POST'])
@login_required
def reject_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Check if user has QC role
    if current_user.role not in ['qc', 'manager', 'admin']:
        flash('You do not have permission to reject GRPO documents.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    grpo_doc.status = 'rejected'
    grpo_doc.qc_user_id = current_user.id
    grpo_doc.qc_notes = request.form.get('qc_notes', '')
    db.session.commit()
    
    # Update all items QC status
    for item in grpo_doc.items:
        item.qc_status = 'rejected'
        item.qc_notes = request.form.get('qc_notes', '')
    db.session.commit()
    
    flash('GRPO rejected!', 'warning')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/inventory_transfer')
@login_required
def inventory_transfer():
    transfers = InventoryTransfer.query.filter_by(user_id=current_user.id).order_by(InventoryTransfer.created_at.desc()).all()
    return render_template('inventory_transfer.html', transfers=transfers)

@app.route('/inventory_transfer/create', methods=['POST'])
@login_required
def create_inventory_transfer():
    transfer_request_number = request.form['transfer_request_number']
    
    # Create inventory transfer
    transfer = InventoryTransfer(
        transfer_request_number=transfer_request_number,
        user_id=current_user.id
    )
    db.session.add(transfer)
    db.session.commit()
    
    flash('Inventory transfer created successfully!', 'success')
    return redirect(url_for('inventory_transfer_detail', transfer_id=transfer.id))

@app.route('/inventory_transfer/<int:transfer_id>')
@login_required
def inventory_transfer_detail(transfer_id):
    transfer = InventoryTransfer.query.get_or_404(transfer_id)
    return render_template('inventory_transfer_detail.html', transfer=transfer)

@app.route('/pick_list')
@login_required
def pick_list():
    pick_lists = PickList.query.filter_by(user_id=current_user.id).order_by(PickList.created_at.desc()).all()
    return render_template('pick_list.html', pick_lists=pick_lists)

@app.route('/pick_list/<int:pick_list_id>')
@login_required
def pick_list_detail(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    return render_template('pick_list_detail.html', pick_list=pick_list)

@app.route('/create_pick_list', methods=['POST'])
@login_required
def create_pick_list():
    sales_order_number = request.form.get('sales_order_number')
    pick_list_number = request.form.get('pick_list_number')
    
    if not sales_order_number or not pick_list_number:
        flash('Sales order number and pick list number are required', 'error')
        return redirect(url_for('pick_list'))
    
    # Create new pick list
    pick_list = PickList(
        sales_order_number=sales_order_number,
        pick_list_number=pick_list_number,
        user_id=current_user.id,
        status='pending'
    )
    
    db.session.add(pick_list)
    db.session.commit()
    
    flash('Pick list created successfully', 'success')
    return redirect(url_for('pick_list_detail', pick_list_id=pick_list.id))

@app.route('/pick_list/<int:pick_list_id>/approve', methods=['POST'])
@login_required
def approve_pick_list(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    
    if current_user.role in ['admin', 'manager']:
        pick_list.status = 'approved'
        pick_list.approver_id = current_user.id
        db.session.commit()
        flash('Pick list approved successfully!', 'success')
    else:
        flash('You do not have permission to approve pick lists.', 'error')
    
    return redirect(url_for('pick_list_detail', pick_list_id=pick_list_id))

@app.route('/pick_list/<int:pick_list_id>/reject', methods=['POST'])
@login_required
def reject_pick_list(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    
    if current_user.role in ['admin', 'manager']:
        pick_list.status = 'rejected'
        pick_list.approver_id = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pick list rejected successfully'})
    else:
        return jsonify({'success': False, 'message': 'You do not have permission to reject pick lists'}), 403

@app.route('/inventory_counting')
@login_required
def inventory_counting():
    counts = InventoryCount.query.filter_by(user_id=current_user.id).order_by(InventoryCount.created_at.desc()).all()
    return render_template('inventory_counting.html', counts=counts)

@app.route('/inventory_counting/<int:count_id>')
@login_required
def inventory_counting_detail(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    return render_template('inventory_counting_detail.html', count=count)

@app.route('/create_count_task', methods=['POST'])
@login_required
def create_count_task():
    count_number = request.form.get('count_number')
    warehouse_code = request.form.get('warehouse_code')
    bin_location = request.form.get('bin_location')
    
    if not count_number or not warehouse_code or not bin_location:
        flash('All fields are required', 'error')
        return redirect(url_for('inventory_counting'))
    
    # Create new count task
    count = InventoryCount(
        count_number=count_number,
        warehouse_code=warehouse_code,
        bin_location=bin_location,
        user_id=current_user.id,
        status='assigned'
    )
    
    db.session.add(count)
    db.session.commit()
    
    flash('Count task created successfully', 'success')
    return redirect(url_for('inventory_counting'))

@app.route('/inventory_counting/<int:count_id>/start', methods=['POST'])
@login_required
def start_count_task(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    
    if count.user_id != current_user.id:
        flash('You can only start your own count tasks', 'error')
        return redirect(url_for('inventory_counting'))
    
    count.status = 'in_progress'
    db.session.commit()
    
    flash('Count task started', 'success')
    return redirect(url_for('inventory_counting_detail', count_id=count_id))

@app.route('/inventory_counting/<int:count_id>/complete', methods=['POST'])
@login_required
def complete_count_task(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    
    if count.user_id != current_user.id:
        flash('You can only complete your own count tasks', 'error')
        return redirect(url_for('inventory_counting'))
    
    count.status = 'completed'
    db.session.commit()
    
    flash('Count task completed successfully', 'success')
    return redirect(url_for('inventory_counting'))

@app.route('/api/pending_approvals')
@login_required
def get_pending_approvals():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    pending_pick_lists = PickList.query.filter_by(status='pending').all()
    
    data = []
    for pick_list in pending_pick_lists:
        data.append({
            'id': pick_list.id,
            'pick_list_number': pick_list.pick_list_number,
            'sales_order_number': pick_list.sales_order_number,
            'user_name': f"{pick_list.user.first_name} {pick_list.user.last_name}",
            'created_at': pick_list.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'pending_approvals': data})

@app.route('/bin_scanning')
@login_required
def bin_scanning():
    return render_template('bin_scanning.html')

@app.route('/api/scan_bin', methods=['POST'])
@login_required
def scan_bin():
    bin_code = request.json['bin_code']
    
    # Get items from SAP B1
    sap = SAPIntegration()
    items = sap.get_bin_items(bin_code)
    
    return jsonify({'items': items})

@app.route('/label_printing')
@login_required
def label_printing():
    return render_template('label_printing.html')

@app.route('/api/print_label', methods=['POST'])
@login_required
def print_label():
    data = request.get_json()
    if not data or 'item_code' not in data:
        return jsonify({'error': 'item_code is required'}), 400
    
    item_code = data['item_code']
    label_format = data.get('label_format', 'standard')
    
    # Generate barcode and print label
    barcode = f"ITM_{item_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save to database
    label = BarcodeLabel(
        item_code=item_code,
        barcode=barcode,
        label_format=label_format,
        print_count=1,
        last_printed=datetime.utcnow()
    )
    db.session.add(label)
    db.session.commit()
    
    return jsonify({'success': True, 'barcode': barcode})

@app.route('/barcode_reprint')
@login_required
def barcode_reprint():
    labels = BarcodeLabel.query.order_by(BarcodeLabel.last_printed.desc()).all()
    return render_template('barcode_reprint.html', labels=labels)

@app.route('/api/reprint_label', methods=['POST'])
@login_required
def reprint_label():
    label_id = request.json['label_id']
    
    label = BarcodeLabel.query.get_or_404(label_id)
    label.print_count += 1
    label.last_printed = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'barcode': label.barcode})

@app.route('/user_management')
@login_required
def user_management():
    if current_user.role != 'admin':
        flash('You do not have permission to access user management.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/user_management/create', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        flash('You do not have permission to create users.', 'error')
        return redirect(url_for('dashboard'))
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('user_management'))
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name=request.form['first_name'],
        last_name=request.form['last_name'],
        role=role
    )
    db.session.add(user)
    db.session.commit()
    
    flash('User created successfully!', 'success')
    return redirect(url_for('user_management'))

# API endpoints for barcode scanning
@app.route('/api/validate_po', methods=['POST'])
@login_required
def validate_po():
    po_number = request.json['po_number']
    
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if po_data:
        return jsonify({'valid': True, 'po_data': po_data})
    else:
        return jsonify({'valid': False, 'error': 'Purchase Order not found'})

@app.route('/api/validate_item', methods=['POST'])
@login_required
def validate_item():
    item_code = request.json['item_code']
    
    sap = SAPIntegration()
    item_data = sap.get_item_master(item_code)
    
    if item_data:
        return jsonify({'valid': True, 'item_data': item_data})
    else:
        return jsonify({'valid': False, 'error': 'Item not found'})

@app.route('/api/get_bins', methods=['GET'])
@login_required
def get_bins():
    warehouse = request.args.get('warehouse')
    
    sap = SAPIntegration()
    bins = sap.get_warehouse_bins(warehouse)
    
    return jsonify({'bins': bins})

# Enhanced GRPO API routes

@app.route('/api/scan_po', methods=['POST'])
@login_required
def scan_po():
    """API endpoint for PO barcode scanning"""
    po_number = request.json.get('po_number')
    
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if po_data:
        return jsonify({
            'success': True,
            'po_data': {
                'po_number': po_data.get('DocNum'),
                'supplier_code': po_data.get('CardCode'),
                'supplier_name': po_data.get('CardName'),
                'po_date': po_data.get('DocDate'),
                'total': po_data.get('DocTotal'),
                'items': po_data.get('DocumentLines', [])
            }
        })
    else:
        return jsonify({'success': False, 'error': 'PO not found'})

@app.route('/api/scan_barcode', methods=['POST'])
@login_required  
def scan_barcode():
    """API endpoint for supplier barcode scanning"""
    barcode = request.json.get('barcode')
    
    # This would integrate with a barcode lookup service or database
    # For now, return mock data
    return jsonify({
        'success': True,
        'item_data': {
            'item_code': 'ITM001',
            'batch_number': 'BTH2025001',
            'expiration_date': '2025-12-31',
            'serial_number': barcode
        }
    })

@app.route('/api/generate_barcode', methods=['POST'])
@login_required
def generate_barcode_api():
    """Generate new barcode for item"""
    item_code = request.json.get('item_code')
    batch_number = request.json.get('batch_number', '')
    
    import uuid
    barcode = f"WMS-{item_code}-{uuid.uuid4().hex[:8].upper()}"
    
    return jsonify({
        'success': True,
        'barcode': barcode
    })

@app.route('/qc_dashboard')
@login_required
def qc_dashboard():
    """QC Dashboard for pending approvals"""
    if current_user.role not in ['qc', 'manager', 'admin']:
        flash('Access denied. QC role required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        pending_grpos = GRPODocument.query.filter_by(status='submitted').order_by(GRPODocument.created_at.desc()).all()
    except Exception as e:
        logging.error(f"Database error in QC dashboard: {e}")
        pending_grpos = []
        flash('Database needs to be updated. Please run: python reset_database.py', 'warning')
    
    return render_template('qc_dashboard.html', pending_grpos=pending_grpos)

@app.route('/api/get_bins_list')
@login_required
def get_bins_api():
    """API endpoint to get available bins"""
    warehouse = request.args.get('warehouse', 'WH01')
    
    # This would integrate with SAP to get real bin data
    bins = [
        {'code': 'A-01-01', 'name': 'Zone A - Rack 01 - Level 01', 'type': 'storage'},
        {'code': 'A-01-02', 'name': 'Zone A - Rack 01 - Level 02', 'type': 'storage'},
        {'code': 'B-01-01', 'name': 'Zone B - Rack 01 - Level 01', 'type': 'quarantine'},
        {'code': 'B-01-02', 'name': 'Zone B - Rack 01 - Level 02', 'type': 'quarantine'},
        {'code': 'C-01-01', 'name': 'Zone C - Rack 01 - Level 01', 'type': 'shipping'},
    ]
    
    return jsonify({'bins': bins})

# Default admin user is created in app.py during initialization
