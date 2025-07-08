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
    
    return render_template('dashboard.html', stats=stats)

@app.route('/grpo')
@login_required
def grpo():
    documents = GRPODocument.query.filter_by(user_id=current_user.id).order_by(GRPODocument.created_at.desc()).all()
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
    
    # Create GRPO document
    grpo_doc = GRPODocument(
        po_number=po_number,
        user_id=current_user.id
    )
    db.session.add(grpo_doc)
    db.session.commit()
    
    flash('GRPO document created successfully!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_doc.id))

@app.route('/grpo/<int:grpo_id>')
@login_required
def grpo_detail(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Get PO items from SAP
    sap = SAPIntegration()
    po_items = sap.get_purchase_order_items(grpo_doc.po_number)
    
    return render_template('grpo_detail.html', grpo_doc=grpo_doc, po_items=po_items)

@app.route('/grpo/<int:grpo_id>/add_item', methods=['POST'])
@login_required
def add_grpo_item(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    item_code = request.form['item_code']
    quantity = float(request.form['quantity'])
    bin_location = request.form['bin_location']
    batch_number = request.form.get('batch_number')
    
    # Create GRPO item
    grpo_item = GRPOItem(
        grpo_document_id=grpo_doc.id,
        item_code=item_code,
        item_name=request.form['item_name'],
        quantity=quantity,
        unit_of_measure=request.form['unit_of_measure'],
        bin_location=bin_location,
        batch_number=batch_number
    )
    db.session.add(grpo_item)
    db.session.commit()
    
    flash('Item added to GRPO successfully!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/submit', methods=['POST'])
@login_required
def submit_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Submit to SAP B1
    sap = SAPIntegration()
    result = sap.create_goods_receipt_po(grpo_doc)
    
    if result['success']:
        grpo_doc.status = 'approved'
        grpo_doc.sap_document_number = result['document_number']
        db.session.commit()
        flash('GRPO submitted successfully to SAP B1!', 'success')
    else:
        flash(f'Error submitting GRPO: {result["error"]}', 'error')
    
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

# Default admin user is created in app.py during initialization
