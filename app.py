"""
Intelligent Mess Management System
Backend API with Flask
Features: Authentication, Meal Booking, Attendance, Billing, Inventory, Feedback, ML Prediction, Reporting
"""

from flask import Flask, request, jsonify, session, render_template, send_file
from flask_cors import CORS
import sqlite3
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
import os
from functools import wraps
# Optional imports with fallback
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("Warning: razorpay module not installed. Payment features will be disabled.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas module not installed. Excel reports will be disabled.")

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib module not installed. Charts will be disabled.")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab module not installed. PDF reports will be disabled.")

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("Warning: qrcode module not installed. QR code features will be disabled.")

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn module not installed. ML prediction will be disabled.")

import io
import base64

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy module not installed. Some features may be disabled.")

from config import Config

app = Flask(__name__, template_folder='.', static_folder='assets')
app.config.from_object(Config)
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:5000', 'http://localhost:5000', 'http://0.0.0.0:5000'])

# Initialize Razorpay client (if available)
razorpay_client = None
if RAZORPAY_AVAILABLE:
    try:
        razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    except Exception as e:
        print(f"Warning: Could not initialize Razorpay client: {e}")
        RAZORPAY_AVAILABLE = False

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database from schema file and run column migrations"""
    conn = get_db_connection()
    try:
        with open('mess_management_schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
            conn.executescript(schema)

        # Safe ALTER TABLE migrations for existing tables
        migrations = [
            "ALTER TABLE users ADD COLUMN roll_number TEXT",
            "ALTER TABLE users ADD COLUMN profile_photo TEXT",
            "ALTER TABLE users ADD COLUMN dietary_pref TEXT DEFAULT 'any'",
            "ALTER TABLE users ADD COLUMN reset_token TEXT",
            "ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP",
            "ALTER TABLE meals ADD COLUMN meal_tag TEXT DEFAULT 'veg'",
            "ALTER TABLE meals ADD COLUMN capacity INTEGER DEFAULT 100",
            "ALTER TABLE meals ADD COLUMN allergens TEXT DEFAULT ''",
            "ALTER TABLE meals ADD COLUMN booking_cutoff_hour INTEGER DEFAULT 8",
        ]
        for sql in migrations:
            try:
                conn.execute(sql)
            except Exception:
                pass  # Column already exists

        # Hash any unhashed passwords
        users = conn.execute('SELECT id, username, password FROM users').fetchall()
        for user in users:
            if not (user['password'].startswith('pbkdf2:') or
                    user['password'].startswith('scrypt:')):
                conn.execute('UPDATE users SET password = ? WHERE id = ?',
                             (hash_password(user['password']), user['id']))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()


def log_audit(user_id, action, resource=None, details=None):
    """Write an entry to audit_log (best-effort, never raises)"""
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO audit_log (user_id, action, resource, details) VALUES (?, ?, ?, ?)',
            (user_id, action, resource, details)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def hash_password(password):
    """Hash password using werkzeug"""
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """Verify password against hash"""
    return check_password_hash(password_hash, password)

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        conn = get_db_connection()
        user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if not user or user['role'] != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Serve login page"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """Serve login page (alternative route)"""
    return render_template('index.html')

@app.route('/signup')
def signup_page():
    """Serve signup page"""
    return render_template('signup.html')

@app.route('/signup.html')
def signup_html():
    """Serve signup page (alternative route)"""
    return render_template('signup.html')

@app.route('/dashboard.html')
def dashboard():
    """Serve dashboard page"""
    return render_template('dashboard.html')

@app.route('/meals.html')
def meals():
    """Serve meals page"""
    return render_template('meals.html')

@app.route('/attendance.html')
def attendance():
    """Serve attendance page"""
    return render_template('attendance.html')

@app.route('/billing.html')
def billing():
    """Serve billing page"""
    return render_template('billing.html')

@app.route('/inventory.html')
def inventory():
    """Serve inventory page"""
    return render_template('inventory.html')

@app.route('/feedback.html')
def feedback():
    """Serve feedback page"""
    return render_template('feedback.html')

@app.route('/users.html')
def users():
    """Serve users page"""
    return render_template('users.html')

@app.route('/reports.html')
def reports():
    """Serve reports page"""
    return render_template('reports.html')

@app.route('/settings.html')
def settings():
    """Serve settings page"""
    return render_template('settings.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role', 'student')
        
        if not all([username, email, password, name]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        conn = get_db_connection()
        # Check if username or email exists
        existing = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
        
        # Insert new user
        password_hash = hash_password(password)
        conn.execute(
            'INSERT INTO users (username, email, password, name, role) VALUES (?, ?, ?, ?, ?)',
            (username, email, password_hash, name, role)
        )
        # Commit and close connection - MUST be inside try block
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and verify_password(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({
                'success': True,
                'role': user['role'],
                'name': user['name'],
                'id': user['id'],
                'username': user['username']
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/current_user')
@login_required
def current_user():
    """Get current logged in user"""
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, name, email, role FROM users WHERE id = ?', 
                       (session['user_id'],)).fetchone()
    conn.close()
    return jsonify(dict(user) if user else {})

# ==================== MEAL MANAGEMENT ROUTES ====================

@app.route('/api/meals')
@login_required
def get_meals():
    """Get all meals (with today's meals highlighted)"""
    try:
        date_filter = request.args.get('date', None)
        conn = get_db_connection()
        
        if date_filter:
            meals = conn.execute(
                'SELECT * FROM meals WHERE date = ? ORDER BY meal_type',
                (date_filter,)
            ).fetchall()
        else:
            meals = conn.execute(
                'SELECT * FROM meals ORDER BY date DESC, meal_type'
            ).fetchall()
        
        conn.close()
        return jsonify([dict(meal) for meal in meals])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meals', methods=['POST'])
@admin_required
def create_meal():
    """Admin: Create new meal"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO meals (date, meal_type, menu_items, price) VALUES (?, ?, ?, ?)',
            (data['date'], data['meal_type'], data['menu_items'], data.get('price', 50.0))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Meal created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/meals/<int:meal_id>', methods=['PUT'])
@admin_required
def update_meal(meal_id):
    """Admin: Update meal"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'UPDATE meals SET date = ?, meal_type = ?, menu_items = ?, price = ? WHERE id = ?',
            (data['date'], data['meal_type'], data['menu_items'], data.get('price', 50.0), meal_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Meal updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/meals/<int:meal_id>', methods=['DELETE'])
@admin_required
def delete_meal(meal_id):
    """Admin: Delete meal"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM meals WHERE id = ?', (meal_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Meal deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== MEAL BOOKING ROUTES ====================

@app.route('/api/bookings')
@login_required
def get_bookings():
    """Get meal bookings (filtered by user if student)"""
    try:
        conn = get_db_connection()
        if session['role'] == 'student':
            bookings = conn.execute('''
                SELECT mb.*, m.date, m.meal_type, m.menu_items, m.price, u.name as user_name
                FROM meal_booking mb
                JOIN meals m ON mb.meal_id = m.id
                JOIN users u ON mb.user_id = u.id
                WHERE mb.user_id = ?
                ORDER BY m.date DESC, m.meal_type
            ''', (session['user_id'],)).fetchall()
        else:
            bookings = conn.execute('''
                SELECT mb.*, m.date, m.meal_type, m.menu_items, m.price, u.name as user_name
                FROM meal_booking mb
                JOIN meals m ON mb.meal_id = m.id
                JOIN users u ON mb.user_id = u.id
                ORDER BY m.date DESC, m.meal_type
            ''').fetchall()
        conn.close()
        return jsonify([dict(b) for b in bookings])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
@login_required
def create_booking():
    """Book a meal"""
    try:
        data = request.json
        meal_id = data.get('meal_id')
        user_id = session['user_id']
        
        conn = get_db_connection()
        # Check if already booked
        existing = conn.execute(
            'SELECT * FROM meal_booking WHERE user_id = ? AND meal_id = ?',
            (user_id, meal_id)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Meal already booked'}), 400
        
        conn.execute(
            'INSERT INTO meal_booking (user_id, meal_id, status) VALUES (?, ?, ?)',
            (user_id, meal_id, 'booked')
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Meal booked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@login_required
def cancel_booking(booking_id):
    """Cancel meal booking"""
    try:
        conn = get_db_connection()
        booking = conn.execute('SELECT * FROM meal_booking WHERE id = ?', (booking_id,)).fetchone()
        
        if not booking:
            conn.close()
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Check if user owns the booking or is admin
        if booking['user_id'] != session['user_id'] and session['role'] != 'admin':
            conn.close()
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        conn.execute(
            'UPDATE meal_booking SET status = ? WHERE id = ?',
            ('cancelled', booking_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Booking cancelled successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ATTENDANCE ROUTES ====================

@app.route('/api/attendance')
@login_required
def get_attendance():
    """Get attendance records"""
    try:
        conn = get_db_connection()
        if session['role'] == 'student':
            attendance = conn.execute('''
                SELECT a.*, m.date, m.meal_type, u.name as user_name
                FROM attendance a
                JOIN meals m ON a.meal_id = m.id
                JOIN users u ON a.user_id = u.id
                WHERE a.user_id = ?
                ORDER BY a.timestamp DESC
            ''', (session['user_id'],)).fetchall()
        else:
            attendance = conn.execute('''
                SELECT a.*, m.date, m.meal_type, u.name as user_name
                FROM attendance a
                JOIN meals m ON a.meal_id = m.id
                JOIN users u ON a.user_id = u.id
                ORDER BY a.timestamp DESC
            ''').fetchall()
        conn.close()
        return jsonify([dict(a) for a in attendance])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/qr/<int:meal_id>')
@login_required
def generate_qr_code(meal_id):
    """Generate QR code for attendance"""
    if not QRCODE_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'QR code generation not available. Please install qrcode module.'
        }), 503
    
    try:
        user_id = session['user_id']
        qr_data = f"{user_id}:{meal_id}:{datetime.now().isoformat()}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_code': f"data:image/png;base64,{img_base64}",
            'qr_data': qr_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/attendance', methods=['POST'])
@login_required
def mark_attendance():
    """Mark attendance (can be QR scan or manual)"""
    try:
        data = request.json
        meal_id = data.get('meal_id')
        user_id = session['user_id']
        qr_data = data.get('qr_data', None)
        
        conn = get_db_connection()
        # Check if attendance already marked
        existing = conn.execute(
            'SELECT * FROM attendance WHERE user_id = ? AND meal_id = ?',
            (user_id, meal_id)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Attendance already marked'}), 400
        
        # Verify booking exists
        booking = conn.execute(
            'SELECT * FROM meal_booking WHERE user_id = ? AND meal_id = ? AND status = ?',
            (user_id, meal_id, 'booked')
        ).fetchone()
        
        if not booking:
            conn.close()
            return jsonify({'success': False, 'message': 'No booking found for this meal'}), 400
        
        conn.execute(
            'INSERT INTO attendance (user_id, meal_id, attendance_status, qr_code) VALUES (?, ?, ?, ?)',
            (user_id, meal_id, 'present', qr_data)
        )
        
        # Update booking status to completed
        conn.execute(
            'UPDATE meal_booking SET status = ? WHERE user_id = ? AND meal_id = ?',
            ('completed', user_id, meal_id)
        )
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== BILLING ROUTES ====================

@app.route('/api/billing')
@login_required
def get_billing():
    """Get billing records"""
    try:
        conn = get_db_connection()
        if session['role'] == 'student':
            bills = conn.execute('''
                SELECT b.*, u.name as user_name
                FROM billing b
                JOIN users u ON b.user_id = u.id
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            ''', (session['user_id'],)).fetchall()
        else:
            bills = conn.execute('''
                SELECT b.*, u.name as user_name
                FROM billing b
                JOIN users u ON b.user_id = u.id
                ORDER BY b.created_at DESC
            ''').fetchall()
        conn.close()
        return jsonify([dict(b) for b in bills])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/billing/calculate', methods=['POST'])
@login_required
def calculate_bill():
    """Calculate bill for a user for a month"""
    try:
        data = request.json
        user_id = data.get('user_id', session['user_id'])
        month = data.get('month')  # Format: "January 2025"
        
        if session['role'] == 'student' and user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        # Get all completed meal bookings for the month
        # Parse month to get date range
        month_num = datetime.strptime(month.split()[0], '%B').month
        year = int(month.split()[1])
        start_date = date(year, month_num, 1)
        if month_num == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month_num + 1, 1)
        
        bookings = conn.execute('''
            SELECT m.price
            FROM meal_booking mb
            JOIN meals m ON mb.meal_id = m.id
            WHERE mb.user_id = ? AND mb.status = 'completed'
            AND m.date >= ? AND m.date < ?
        ''', (user_id, start_date, end_date)).fetchall()
        
        total_amount = sum(b['price'] for b in bookings)
        
        # Check if bill exists
        existing = conn.execute(
            'SELECT * FROM billing WHERE user_id = ? AND month = ?',
            (user_id, month)
        ).fetchone()
        
        if existing:
            conn.execute(
                'UPDATE billing SET total_amount = ? WHERE id = ?',
                (total_amount, existing['id'])
            )
            bill_id = existing['id']
        else:
            cursor = conn.execute(
                'INSERT INTO billing (user_id, month, total_amount, payment_status) VALUES (?, ?, ?, ?)',
                (user_id, month, total_amount, 'Pending')
            )
            bill_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'bill_id': bill_id, 'total_amount': total_amount})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== PAYMENT GATEWAY ROUTES ====================

@app.route('/api/payment/create_order', methods=['POST'])
@login_required
def create_payment_order():
    """Create Razorpay order"""
    if not RAZORPAY_AVAILABLE or razorpay_client is None:
        return jsonify({'success': False, 'message': 'Payment gateway not available. Please install razorpay module.'}), 503
    
    try:
        data = request.json
        amount = float(data.get('amount'))  # Amount in rupees
        bill_id = data.get('bill_id')
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400
        
        # Create Razorpay order (amount in paise)
        order = razorpay_client.order.create({
            'amount': int(amount * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': f'bill_{bill_id}',
            'notes': {
                'bill_id': bill_id,
                'user_id': session['user_id']
            }
        })
        
        # Store order in database
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO payment_transactions (user_id, bill_id, amount, razorpay_order_id, status) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], bill_id, amount, order['id'], 'pending')
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'key': app.config['RAZORPAY_KEY_ID']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    """Verify Razorpay payment"""
    if not RAZORPAY_AVAILABLE or razorpay_client is None:
        return jsonify({'success': False, 'message': 'Payment gateway not available. Please install razorpay module.'}), 503
    
    try:
        data = request.json
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        bill_id = data.get('bill_id')
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return jsonify({'success': False, 'message': 'Payment verification failed'}), 400
        
        # Update database
        conn = get_db_connection()
        conn.execute(
            'UPDATE payment_transactions SET razorpay_payment_id = ?, status = ? WHERE razorpay_order_id = ?',
            (razorpay_payment_id, 'success', razorpay_order_id)
        )
        conn.execute(
            'UPDATE billing SET payment_status = ?, payment_date = ?, razorpay_order_id = ?, razorpay_payment_id = ? WHERE id = ?',
            ('Paid', date.today(), razorpay_order_id, razorpay_payment_id, bill_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Payment verified and updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/billing/<int:bill_id>', methods=['PUT'])
@admin_required
def update_bill(bill_id):
    """Admin: Update a bill (amount, status, payment date)"""
    try:
        data = request.json
        conn = get_db_connection()
        bill = conn.execute('SELECT id FROM billing WHERE id = ?', (bill_id,)).fetchone()
        if not bill:
            conn.close()
            return jsonify({'success': False, 'message': 'Bill not found'}), 404
        conn.execute(
            'UPDATE billing SET total_amount=?, payment_status=?, payment_date=? WHERE id=?',
            (data.get('total_amount'), data.get('payment_status'), data.get('payment_date'), bill_id)
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'update_bill', 'billing', f'bill {bill_id}')
        return jsonify({'success': True, 'message': 'Bill updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/billing/<int:bill_id>', methods=['DELETE'])
@admin_required
def delete_bill(bill_id):
    """Admin: Delete a bill"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM billing WHERE id=?', (bill_id,))
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'delete_bill', 'billing', f'bill {bill_id}')
        return jsonify({'success': True, 'message': 'Bill deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== INVENTORY ROUTES ====================

@app.route('/api/inventory')
@admin_required
def get_inventory():
    """Get inventory items (admin only)"""
    try:
        conn = get_db_connection()
        items = conn.execute('SELECT * FROM inventory ORDER BY item_name').fetchall()
        conn.close()
        
        # Check for low stock
        result = []
        for item in items:
            item_dict = dict(item)
            item_dict['low_stock'] = item['quantity'] <= item['threshold']
            result.append(item_dict)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inventory', methods=['POST'])
@admin_required
def create_inventory_item():
    """Admin: Add inventory item"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO inventory (item_name, quantity, unit, threshold, category) VALUES (?, ?, ?, ?, ?)',
            (data['item_name'], data['quantity'], data['unit'], data.get('threshold', 10.0), data.get('category', 'general'))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Inventory item added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@admin_required
def update_inventory_item(item_id):
    """Admin: Update inventory item"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'UPDATE inventory SET item_name = ?, quantity = ?, unit = ?, threshold = ?, category = ?, last_updated = ? WHERE id = ?',
            (data['item_name'], data['quantity'], data['unit'], data.get('threshold', 10.0), 
             data.get('category', 'general'), date.today(), item_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Inventory updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_inventory_item(item_id):
    """Admin: Delete inventory item"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Inventory item deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FEEDBACK ROUTES ====================

@app.route('/api/feedback')
@login_required
def get_feedback():
    """Get feedback records"""
    try:
        conn = get_db_connection()
        if session['role'] == 'student':
            feedback = conn.execute('''
                SELECT f.*, u.name as user_name, m.meal_type, m.date
                FROM feedback f
                JOIN users u ON f.user_id = u.id
                LEFT JOIN meals m ON f.meal_id = m.id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
            ''', (session['user_id'],)).fetchall()
        else:
            feedback = conn.execute('''
                SELECT f.*, u.name as user_name, m.meal_type, m.date
                FROM feedback f
                JOIN users u ON f.user_id = u.id
                LEFT JOIN meals m ON f.meal_id = m.id
                ORDER BY f.created_at DESC
            ''').fetchall()
        conn.close()
        return jsonify([dict(f) for f in feedback])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
@login_required
def create_feedback():
    """Submit feedback"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO feedback (user_id, meal_id, message, rating) VALUES (?, ?, ?, ?)',
            (session['user_id'], data.get('meal_id'), data['message'], data.get('rating', 3))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ANALYTICS & ML PREDICTION ====================

@app.route('/api/analytics/dashboard')
@login_required
def get_dashboard_analytics():
    """Get dashboard analytics (admin) or student summary (student)"""
    try:
        conn = get_db_connection()
        today = date.today()
        user_role = session['role']
        user_id = session['user_id']
        
        if user_role == 'admin':
            # Admin dashboard analytics
            total_students = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('student',)).fetchone()['count']
            
            today_bookings = conn.execute(
                'SELECT COUNT(*) as count FROM meal_booking mb JOIN meals m ON mb.meal_id = m.id WHERE m.date = ? AND mb.status = ?',
                (today, 'booked')
            ).fetchone()['count']
            
            pending_payments = conn.execute(
                "SELECT COUNT(*) as count FROM billing WHERE payment_status = 'Pending'"
            ).fetchone()['count']
            
            low_stock = conn.execute(
                'SELECT COUNT(*) as count FROM inventory WHERE quantity <= threshold'
            ).fetchone()['count']
            
            recent_feedback = conn.execute(
                'SELECT COUNT(*) as count FROM feedback WHERE DATE(created_at) = ?',
                (today,)
            ).fetchone()['count']
            
            conn.close()
            
            return jsonify({
                'role': 'admin',
                'total_students': total_students,
                'today_bookings': today_bookings,
                'pending_payments': pending_payments,
                'low_stock_items': low_stock,
                'recent_feedback': recent_feedback
            })
        else:
            # Student dashboard summary
            my_today_bookings = conn.execute(
                'SELECT COUNT(*) as count FROM meal_booking mb JOIN meals m ON mb.meal_id = m.id WHERE mb.user_id = ? AND m.date = ? AND mb.status = ?',
                (user_id, today, 'booked')
            ).fetchone()['count']
            
            upcoming_meals = conn.execute(
                'SELECT COUNT(*) as count FROM meal_booking mb JOIN meals m ON mb.meal_id = m.id WHERE mb.user_id = ? AND m.date >= ? AND mb.status = ?',
                (user_id, today, 'booked')
            ).fetchone()['count']
            
            pending_bills = conn.execute(
                "SELECT COUNT(*) as count FROM billing WHERE user_id = ? AND payment_status = 'Pending'",
                (user_id,)
            ).fetchone()['count']
            
            total_spent = conn.execute(
                "SELECT COALESCE(SUM(total_amount), 0) as total FROM billing WHERE user_id = ? AND payment_status = 'Paid'",
                (user_id,)
            ).fetchone()['total'] or 0
            
            recent_attendance = conn.execute(
                'SELECT COUNT(*) as count FROM attendance a JOIN meals m ON a.meal_id = m.id WHERE a.user_id = ? AND m.date >= ? AND a.attendance_status = ?',
                (user_id, date.today() - timedelta(days=7), 'present')
            ).fetchone()['count']
            
            conn.close()
            
            return jsonify({
                'role': 'student',
                'today_bookings': my_today_bookings,
                'upcoming_meals': upcoming_meals,
                'pending_bills': pending_bills,
                'total_spent': float(total_spent),
                'recent_attendance': recent_attendance
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/predict_meals')
@admin_required
def predict_meals():
    """ML Model to predict meal count for next day"""
    if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'ML libraries not available. Please install scikit-learn and numpy modules.'
        }), 503
    
    try:
        conn = get_db_connection()
        
        # Get historical attendance data (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Aggregate daily meal counts
        historical_data = conn.execute('''
            SELECT m.date, m.meal_type, COUNT(a.id) as attendance_count
            FROM meals m
            LEFT JOIN attendance a ON m.id = a.meal_id AND a.attendance_status = 'present'
            WHERE m.date >= ? AND m.date <= ?
            GROUP BY m.date, m.meal_type
            ORDER BY m.date
        ''', (start_date, end_date)).fetchall()
        
        conn.close()
        
        if len(historical_data) < 7:
            return jsonify({
                'success': True,
                'prediction': 'Insufficient data for prediction',
                'recommendation': 'Need at least 7 days of data'
            })
        
        # Prepare data for ML
        dates = [datetime.strptime(row['date'], '%Y-%m-%d').date() for row in historical_data]
        day_numbers = [(d - start_date).days for d in dates]
        meal_counts = [row['attendance_count'] for row in historical_data]
        
        # Train simple linear regression model
        X = np.array(day_numbers).reshape(-1, 1)
        y = np.array(meal_counts)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict for next day
        next_day = (end_date - start_date).days + 1
        prediction = model.predict([[next_day]])[0]
        prediction = max(0, int(prediction))  # Ensure non-negative
        
        # Group by meal type
        meal_type_counts = {}
        for row in historical_data:
            meal_type = row['meal_type']
            if meal_type not in meal_type_counts:
                meal_type_counts[meal_type] = []
            meal_type_counts[meal_type].append(row['attendance_count'])
        
        # Average prediction per meal type
        predictions_by_type = {}
        for meal_type, counts in meal_type_counts.items():
            avg_count = sum(counts) / len(counts) if counts else 0
            predictions_by_type[meal_type] = max(0, int(avg_count))
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'predictions_by_type': predictions_by_type,
            'model_score': float(model.score(X, y)) if len(X) > 0 else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== REPORTING ROUTES ====================

@app.route('/api/reports/daily_meal_count')
@admin_required
def generate_daily_meal_report():
    """Generate daily meal count report (PDF)"""
    if not REPORTLAB_AVAILABLE:
        return jsonify({'error': 'PDF generation not available. Please install reportlab module.'}), 503
    
    try:
        start_date = request.args.get('start_date', str(date.today() - timedelta(days=7)))
        end_date = request.args.get('end_date', str(date.today()))
        
        conn = get_db_connection()
        data = conn.execute('''
            SELECT m.date, m.meal_type, COUNT(a.id) as count
            FROM meals m
            LEFT JOIN attendance a ON m.id = a.meal_id AND a.attendance_status = 'present'
            WHERE m.date >= ? AND m.date <= ?
            GROUP BY m.date, m.meal_type
            ORDER BY m.date, m.meal_type
        ''', (start_date, end_date)).fetchall()
        conn.close()
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Daily Meal Count Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Date range
        date_info = Paragraph(f"Date Range: {start_date} to {end_date}", styles['Normal'])
        story.append(date_info)
        story.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [['Date', 'Meal Type', 'Count']]
        for row in data:
            table_data.append([row['date'], row['meal_type'], str(row['count'])])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, 
                        download_name=f'daily_meal_report_{start_date}_to_{end_date}.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/payment_report')
@admin_required
def generate_payment_report():
    """Generate payment report (Excel)"""
    if not PANDAS_AVAILABLE:
        return jsonify({'error': 'Excel generation not available. Please install pandas and openpyxl modules.'}), 503
    
    try:
        month = request.args.get('month', None)
        
        conn = get_db_connection()
        if month:
            bills = conn.execute('''
                SELECT b.*, u.name as user_name, u.email
                FROM billing b
                JOIN users u ON b.user_id = u.id
                WHERE b.month = ?
                ORDER BY b.payment_status, u.name
            ''', (month,)).fetchall()
        else:
            bills = conn.execute('''
                SELECT b.*, u.name as user_name, u.email
                FROM billing b
                JOIN users u ON b.user_id = u.id
                ORDER BY b.month DESC, b.payment_status
            ''').fetchall()
        conn.close()
        
        # Create DataFrame
        df_data = []
        for bill in bills:
            df_data.append({
                'Bill ID': bill['id'],
                'User Name': bill['user_name'],
                'Email': bill['email'],
                'Month': bill['month'],
                'Amount (₹)': bill['total_amount'],
                'Payment Status': bill['payment_status'],
                'Payment Date': bill['payment_date'] or 'N/A',
                'Created At': bill['created_at']
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel file
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Payment Report', index=False)
            worksheet = writer.sheets['Payment Report']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        filename = f'payment_report_{month or "all"}.xlsx'
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/inventory_usage')
@admin_required
def generate_inventory_report():
    """Generate inventory usage report with chart"""
    if not MATPLOTLIB_AVAILABLE:
        return jsonify({'error': 'Chart generation not available. Please install matplotlib module.'}), 503
    
    try:
        conn = get_db_connection()
        items = conn.execute('SELECT * FROM inventory ORDER BY category, item_name').fetchall()
        conn.close()
        
        # Create chart
        item_names = [item['item_name'] for item in items]
        quantities = [item['quantity'] for item in items]
        
        plt.figure(figsize=(10, 6))
        plt.barh(item_names, quantities, color=['red' if q <= items[i]['threshold'] else 'green' for i, q in enumerate(quantities)])
        plt.xlabel('Quantity')
        plt.title('Inventory Status Report')
        plt.tight_layout()
        
        chart_buffer = io.BytesIO()
        plt.savefig(chart_buffer, format='png', dpi=100)
        plt.close()
        chart_buffer.seek(0)
        
        return send_file(chart_buffer, mimetype='image/png', as_attachment=True,
                        download_name='inventory_chart.png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== USER MANAGEMENT ROUTES ====================

@app.route('/api/users')
@admin_required
def get_users():
    """Admin: Get all users"""
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT id, username, name, email, role, status, created_at FROM users ORDER BY role, name').fetchall()
        conn.close()
        return jsonify([dict(user) for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Admin: Update user"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET name = ?, email = ?, role = ?, status = ? WHERE id = ?',
            (data['name'], data['email'], data['role'], data.get('status', 'active'), user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'User updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



# ==================== PROFILE ROUTES ====================

@app.route('/api/profile')
@login_required
def get_profile():
    """Get current user profile"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, name, email, role, roll_number, profile_photo, dietary_pref, created_at FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    return jsonify(dict(user) if user else {})

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user profile"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET name=?, email=?, roll_number=?, dietary_pref=? WHERE id=?',
            (data.get('name'), data.get('email'), data.get('roll_number'),
             data.get('dietary_pref', 'any'), session['user_id'])
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'profile_update', 'users')
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== PASSWORD RESET ROUTES ====================

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    """Generate password reset token (logs token; no email in demo)"""
    try:
        import secrets
        data = request.json
        email = data.get('email')
        conn = get_db_connection()
        user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'Email not found'}), 404
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        conn.execute('UPDATE users SET reset_token=?, reset_token_expiry=? WHERE id=?',
                     (token, expiry, user['id']))
        conn.commit()
        conn.close()
        print(f"[PASSWORD RESET] Token for {email}: {token}")  # In prod: send email
        return jsonify({'success': True, 'message': 'Reset token generated (check server log)', 'token': token})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, reset_token_expiry FROM users WHERE reset_token = ?', (token,)
        ).fetchone()
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 400
        if datetime.now() > datetime.fromisoformat(user['reset_token_expiry']):
            conn.close()
            return jsonify({'success': False, 'message': 'Token has expired'}), 400
        conn.execute(
            'UPDATE users SET password=?, reset_token=NULL, reset_token_expiry=NULL WHERE id=?',
            (hash_password(new_password), user['id'])
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Password reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== MEAL RATINGS ROUTES ====================

@app.route('/api/meals/<int:meal_id>/rate', methods=['POST'])
@login_required
def rate_meal(meal_id):
    """Submit quick rating for a meal"""
    try:
        data = request.json
        rating = int(data.get('rating', 3))
        if not 1 <= rating <= 5:
            return jsonify({'success': False, 'message': 'Rating must be 1-5'}), 400
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO meal_ratings (user_id, meal_id, rating) VALUES (?, ?, ?)',
                (session['user_id'], meal_id, rating)
            )
        except Exception:
            conn.execute(
                'UPDATE meal_ratings SET rating=? WHERE user_id=? AND meal_id=?',
                (rating, session['user_id'], meal_id)
            )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Rating submitted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/meals/<int:meal_id>/rating')
@login_required
def get_meal_rating(meal_id):
    """Get average rating for a meal"""
    try:
        conn = get_db_connection()
        result = conn.execute(
            'SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM meal_ratings WHERE meal_id=?',
            (meal_id,)
        ).fetchone()
        conn.close()
        return jsonify({'avg_rating': round(result['avg_rating'] or 0, 1), 'count': result['count']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ANNOUNCEMENT ROUTES ====================

@app.route('/api/announcements')
@login_required
def get_announcements():
    """Get all announcements"""
    try:
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT a.*, u.name as author_name
            FROM announcements a JOIN users u ON a.created_by = u.id
            ORDER BY a.created_at DESC
        ''').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/announcements', methods=['POST'])
@admin_required
def create_announcement():
    """Admin: Create announcement"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO announcements (title, message, priority, created_by) VALUES (?, ?, ?, ?)',
            (data['title'], data['message'], data.get('priority', 'medium'), session['user_id'])
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'create_announcement', 'announcements', data['title'])
        return jsonify({'success': True, 'message': 'Announcement created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/announcements/<int:ann_id>', methods=['DELETE'])
@admin_required
def delete_announcement(ann_id):
    """Admin: Delete announcement"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM announcements WHERE id=?', (ann_id,))
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'delete_announcement', 'announcements', str(ann_id))
        return jsonify({'success': True, 'message': 'Announcement deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== NOTIFICATION ROUTES ====================

@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get notifications for current user"""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            'SELECT * FROM notifications WHERE user_id=? OR user_id IS NULL ORDER BY created_at DESC LIMIT 30',
            (session['user_id'],)
        ).fetchall()
        unread = sum(1 for r in rows if not r['is_read'])
        conn.close()
        return jsonify({'notifications': [dict(r) for r in rows], 'unread_count': unread})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notif_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notif_id):
    """Mark notification as read"""
    try:
        conn = get_db_connection()
        conn.execute('UPDATE notifications SET is_read=1 WHERE id=?', (notif_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/read_all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        conn = get_db_connection()
        conn.execute(
            'UPDATE notifications SET is_read=1 WHERE user_id=? OR user_id IS NULL',
            (session['user_id'],)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/broadcast', methods=['POST'])
@admin_required
def broadcast_notification():
    """Admin: Send notification to all students"""
    try:
        data = request.json
        conn = get_db_connection()
        students = conn.execute("SELECT id FROM users WHERE role='student'").fetchall()
        for s in students:
            conn.execute(
                'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
                (s['id'], data['message'], data.get('type', 'info'))
            )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Sent to {len(students)} students'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== AUDIT LOG ROUTES ====================

@app.route('/api/audit_log')
@admin_required
def get_audit_log():
    """Admin: Get audit log (paginated)"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT al.*, u.username
            FROM audit_log al LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.timestamp DESC LIMIT ? OFFSET ?
        ''', (per_page, offset)).fetchall()
        total = conn.execute('SELECT COUNT(*) as c FROM audit_log').fetchone()['c']
        conn.close()
        return jsonify({'log': [dict(r) for r in rows], 'total': total, 'page': page, 'per_page': per_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== MESS SETTINGS ROUTES ====================

@app.route('/api/settings')
@login_required
def get_mess_settings():
    """Get all mess settings"""
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM mess_settings ORDER BY key').fetchall()
        conn.close()
        return jsonify({r['key']: r['value'] for r in rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/<key>', methods=['PUT'])
@admin_required
def update_setting(key):
    """Admin: Update a mess setting"""
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO mess_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) '
            'ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP',
            (key, str(data.get('value', '')))
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'update_setting', 'mess_settings', f'{key}={data.get("value")}')
        return jsonify({'success': True, 'message': f'Setting {key} updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SUPPLIER ROUTES ====================

@app.route('/api/suppliers')
@login_required
def get_suppliers():
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/suppliers', methods=['POST'])
@admin_required
def create_supplier():
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO suppliers (name, contact, email, address, category) VALUES (?, ?, ?, ?, ?)',
            (data['name'], data.get('contact'), data.get('email'), data.get('address'), data.get('category', 'general'))
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'create_supplier', 'suppliers', data['name'])
        return jsonify({'success': True, 'message': 'Supplier added'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@admin_required
def update_supplier(supplier_id):
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            'UPDATE suppliers SET name=?, contact=?, email=?, address=?, category=?, status=? WHERE id=?',
            (data['name'], data.get('contact'), data.get('email'), data.get('address'),
             data.get('category', 'general'), data.get('status', 'active'), supplier_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Supplier updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@admin_required
def delete_supplier(supplier_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM suppliers WHERE id=?', (supplier_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Supplier deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== BILLING ENHANCEMENTS ====================

@app.route('/api/billing/<int:bill_id>/pdf')
@login_required
def download_bill_pdf(bill_id):
    """Download bill as PDF"""
    if not REPORTLAB_AVAILABLE:
        return jsonify({'error': 'PDF generation not available'}), 503
    try:
        conn = get_db_connection()
        bill = conn.execute('''
            SELECT b.*, u.name as user_name, u.email, u.roll_number
            FROM billing b JOIN users u ON b.user_id = u.id WHERE b.id = ?
        ''', (bill_id,)).fetchone()
        conn.close()
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        if session['role'] == 'student' and bill['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Intelligent Mess Management System", styles['Title']))
        story.append(Paragraph("BILL RECEIPT", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        tdata = [
            ['Field', 'Value'],
            ['Student Name', bill['user_name']],
            ['Roll Number', bill['roll_number'] or 'N/A'],
            ['Email', bill['email']],
            ['Month', bill['month']],
            ['Total Amount', f"Rs. {bill['total_amount']:.2f}"],
            ['Payment Status', bill['payment_status']],
            ['Payment Date', bill['payment_date'] or 'Pending'],
        ]
        t = Table(tdata, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f0f4f8')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        story.append(t)
        doc.build(story)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=True,
                         download_name=f'bill_{bill_id}_{bill["month"].replace(" ", "_")}.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/billing/generate_monthly', methods=['POST'])
@admin_required
def generate_monthly_bills():
    """Auto-generate bills for all students for a given month"""
    try:
        data = request.json
        month = data.get('month')  # e.g. "March 2026"
        month_num = datetime.strptime(month.split()[0], '%B').month
        year = int(month.split()[1])
        start_date = date(year, month_num, 1)
        end_date = date(year, month_num + 1, 1) if month_num < 12 else date(year + 1, 1, 1)
        conn = get_db_connection()
        students = conn.execute("SELECT id FROM users WHERE role='student' AND status='active'").fetchall()
        created = 0
        for s in students:
            bookings = conn.execute('''
                SELECT SUM(m.price) as total FROM meal_booking mb
                JOIN meals m ON mb.meal_id = m.id
                WHERE mb.user_id=? AND mb.status='completed' AND m.date>=? AND m.date<?
            ''', (s['id'], start_date, end_date)).fetchone()
            total = bookings['total'] or 0.0
            existing = conn.execute(
                'SELECT id FROM billing WHERE user_id=? AND month=?', (s['id'], month)
            ).fetchone()
            if existing:
                conn.execute('UPDATE billing SET total_amount=? WHERE id=?', (total, existing['id']))
            else:
                conn.execute(
                    'INSERT INTO billing (user_id, month, total_amount, payment_status) VALUES (?, ?, ?, ?)',
                    (s['id'], month, total, 'Pending')
                )
                created += 1
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'generate_monthly_bills', 'billing', month)
        return jsonify({'success': True, 'message': f'Bills generated for {len(students)} students ({created} new)'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== INVENTORY DEDUCTION ====================

@app.route('/api/inventory/deduct', methods=['POST'])
@admin_required
def deduct_inventory():
    """Admin: Manually deduct inventory quantity"""
    try:
        data = request.json
        item_id = data.get('item_id')
        amount = float(data.get('amount', 0))
        conn = get_db_connection()
        conn.execute(
            'UPDATE inventory SET quantity = MAX(0, quantity - ?), last_updated = ? WHERE id = ?',
            (amount, date.today(), item_id)
        )
        conn.commit()
        conn.close()
        log_audit(session['user_id'], 'inventory_deduct', 'inventory', f'item {item_id} by {amount}')
        return jsonify({'success': True, 'message': f'Deducted {amount} from inventory item {item_id}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== CSV EXPORT ROUTES ====================

@app.route('/api/export/<resource>')
@admin_required
def export_csv(resource):
    """Export any resource table as CSV"""
    if not PANDAS_AVAILABLE:
        return jsonify({'error': 'pandas not available'}), 503
    allowed = {'meals': 'meals', 'users': 'users', 'billing': 'billing',
               'attendance': 'attendance', 'inventory': 'inventory', 'feedback': 'feedback'}
    if resource not in allowed:
        return jsonify({'error': 'Unknown resource'}), 400
    try:
        conn = get_db_connection()
        rows = conn.execute(f'SELECT * FROM {allowed[resource]}').fetchall()
        conn.close()
        df = pd.DataFrame([dict(r) for r in rows])
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(buf, mimetype='text/csv', as_attachment=True,
                         download_name=f'{resource}_export.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ENHANCED REPORTS ====================

@app.route('/api/reports/student_attendance')
@admin_required
def student_attendance_report():
    """Per-student attendance percentage"""
    try:
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT u.id, u.name, u.roll_number,
                   COUNT(mb.id) as total_booked,
                   SUM(CASE WHEN a.attendance_status='present' THEN 1 ELSE 0 END) as attended
            FROM users u
            LEFT JOIN meal_booking mb ON u.id = mb.user_id AND mb.status != 'cancelled'
            LEFT JOIN attendance a ON mb.user_id = a.user_id AND mb.meal_id = a.meal_id
            WHERE u.role = 'student'
            GROUP BY u.id, u.name, u.roll_number
        ''').fetchall()
        conn.close()
        result = []
        for r in rows:
            booked = r['total_booked'] or 0
            attended = r['attended'] or 0
            pct = round((attended / booked * 100) if booked > 0 else 0, 1)
            result.append({
                'student_id': r['id'], 'name': r['name'], 'roll_number': r['roll_number'],
                'total_booked': booked, 'attended': attended, 'attendance_pct': pct
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/revenue')
@admin_required
def revenue_report():
    """Monthly revenue vs meals served"""
    try:
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT month, 
                   SUM(total_amount) as total_billed,
                   SUM(CASE WHEN payment_status='Paid' THEN total_amount ELSE 0 END) as collected,
                   COUNT(*) as bill_count
            FROM billing GROUP BY month ORDER BY month DESC LIMIT 12
        ''').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== IMPROVED ML PREDICTION ====================

@app.route('/api/ml/predict_meals_v2')
@admin_required
def predict_meals_v2():
    """Day-of-week aware meal prediction"""
    if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
        return jsonify({'success': False, 'message': 'ML libraries not available'}), 503
    try:
        conn = get_db_connection()
        end_date = date.today()
        start_date = end_date - timedelta(days=60)
        historical = conn.execute('''
            SELECT m.date, m.meal_type, COUNT(a.id) as count
            FROM meals m LEFT JOIN attendance a ON m.id=a.meal_id AND a.attendance_status='present'
            WHERE m.date>=? AND m.date<=?
            GROUP BY m.date, m.meal_type ORDER BY m.date
        ''', (start_date, end_date)).fetchall()
        conn.close()
        if len(historical) < 7:
            return jsonify({'success': True, 'prediction': 'Insufficient data', 'recommendation': 'Need 7+ days'})
        rows = []
        for r in historical:
            d = datetime.strptime(r['date'], '%Y-%m-%d').date()
            rows.append({'day_num': (d - start_date).days, 'weekday': d.weekday(), 'count': r['count']})
        X = np.array([[r['day_num'], r['weekday']] for r in rows])
        y = np.array([r['count'] for r in rows])
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        tomorrow = date.today() + timedelta(days=1)
        next_day_num = (tomorrow - start_date).days
        pred = max(0, int(model.predict([[next_day_num, tomorrow.weekday()]])[0]))
        return jsonify({
            'success': True, 'prediction': pred,
            'date': str(tomorrow), 'weekday': tomorrow.strftime('%A'),
            'model_score': round(float(model.score(X, y)), 3)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ml/menu_recommendation')
@admin_required
def menu_recommendation():
    """Recommend top-rated menu items based on feedback"""
    try:
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT m.menu_items, m.meal_type, AVG(mr.rating) as avg_rating, COUNT(mr.id) as votes
            FROM meal_ratings mr JOIN meals m ON mr.meal_id = m.id
            GROUP BY m.id ORDER BY avg_rating DESC, votes DESC LIMIT 10
        ''').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PROFILE PAGE ROUTE ====================

# ==================== FOOD QUANTITY OPTIMIZATION ====================

# Per-head ingredient quantities in grams (configurable per meal type)
FOOD_QUANTITIES_PER_HEAD = {
    'breakfast': {
        'Rice / Poha / Upma (staple)': 150,
        'Milk / Tea / Coffee (liquid)': 250,   # ml
        'Bread / Roti': 80,
        'Vegetables (sabzi)': 60,
        'Oil / Ghee': 10,
        'Salt & Spices mix': 5,
        'Sugar': 15,
    },
    'lunch': {
        'Rice': 200,
        'Dal / Lentils (dry)': 80,
        'Vegetables (sabzi)': 120,
        'Roti / Chapati flour': 120,
        'Curd / Yogurt': 100,   # ml
        'Oil / Ghee': 20,
        'Salt & Spices mix': 8,
        'Salad (tomato, onion, cucumber)': 80,
    },
    'dinner': {
        'Rice': 180,
        'Dal / Lentils (dry)': 70,
        'Roti / Chapati flour': 140,
        'Vegetables / Curry': 130,
        'Oil / Ghee': 20,
        'Salt & Spices mix': 8,
        'Dessert / Sweet': 50,
    },
}

# Waste buffer: recommend 10% extra to avoid shortage
WASTE_BUFFER_PCT = 10

@app.route('/api/ml/food_optimization')
@admin_required
def food_optimization():
    """
    Convert predicted meal count → ingredient quantities with waste buffer.
    Query params:
      meal_count  – int (from prediction or manual entry)
      meal_type   – breakfast | lunch | dinner (default: all)
    """
    try:
        meal_count = int(request.args.get('meal_count', 0))
        meal_type  = request.args.get('meal_type', 'all').lower()

        if meal_count <= 0:
            # Fall back to latest v2 prediction
            conn = get_db_connection()
            if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
                end_date   = date.today()
                start_date = end_date - timedelta(days=60)
                historical = conn.execute('''
                    SELECT m.date, COUNT(a.id) as count
                    FROM meals m
                    LEFT JOIN attendance a ON m.id=a.meal_id AND a.attendance_status='present'
                    WHERE m.date>=? AND m.date<=?
                    GROUP BY m.date ORDER BY m.date
                ''', (start_date, end_date)).fetchall()
                conn.close()
                if len(historical) >= 7:
                    rows_data = []
                    for r in historical:
                        d = datetime.strptime(r['date'], '%Y-%m-%d').date()
                        rows_data.append({'day_num': (d - start_date).days, 'weekday': d.weekday(), 'count': r['count']})
                    X = np.array([[r['day_num'], r['weekday']] for r in rows_data])
                    y = np.array([r['count'] for r in rows_data])
                    from sklearn.linear_model import LinearRegression as LR
                    m_model = LR()
                    m_model.fit(X, y)
                    tomorrow = date.today() + timedelta(days=1)
                    meal_count = max(1, int(m_model.predict([[( tomorrow - start_date).days, tomorrow.weekday()]])[0]))
                else:
                    meal_count = 50  # safe default
            else:
                conn.close()
                meal_count = 50

        # Determine which meal types to compute
        if meal_type == 'all':
            types_to_compute = ['breakfast', 'lunch', 'dinner']
        elif meal_type in FOOD_QUANTITIES_PER_HEAD:
            types_to_compute = [meal_type]
        else:
            return jsonify({'success': False, 'message': 'Invalid meal_type. Use breakfast, lunch, dinner, or all'}), 400

        result = {}
        for mt in types_to_compute:
            quantities = FOOD_QUANTITIES_PER_HEAD[mt]
            buffered_count = int(meal_count * (1 + WASTE_BUFFER_PCT / 100))
            ingredients = []
            for ingredient, grams_per_head in quantities.items():
                unit = 'mL' if 'liquid' in ingredient.lower() or 'milk' in ingredient.lower() or 'curd' in ingredient.lower() else 'g'
                total_grams = grams_per_head * buffered_count
                if unit == 'g' and total_grams >= 1000:
                    display = f"{total_grams / 1000:.2f} kg"
                elif unit == 'mL' and total_grams >= 1000:
                    display = f"{total_grams / 1000:.2f} L"
                else:
                    display = f"{total_grams} {unit}"
                ingredients.append({
                    'ingredient': ingredient,
                    'per_head_g': grams_per_head,
                    'unit': unit,
                    'total_raw': total_grams,
                    'total_display': display,
                })
            result[mt] = {
                'predicted_students': meal_count,
                'buffered_count': buffered_count,
                'buffer_pct': WASTE_BUFFER_PCT,
                'ingredients': ingredients,
            }

        return jsonify({'success': True, 'meal_count': meal_count, 'optimization': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== WASTE ANALYSIS ====================

@app.route('/api/reports/waste_analysis')
@admin_required
def waste_analysis():
    """
    Compare food prepared (booked meals) vs food consumed (attended meals).
    Returns per-day waste percentage + overall summary.
    Query params:
      start_date  – YYYY-MM-DD (default: 30 days ago)
      end_date    – YYYY-MM-DD (default: today)
    """
    try:
        end_date_str   = request.args.get('end_date',   str(date.today()))
        start_date_str = request.args.get('start_date', str(date.today() - timedelta(days=30)))

        conn = get_db_connection()
        rows = conn.execute('''
            SELECT
                m.date,
                m.meal_type,
                COUNT(DISTINCT mb.id)  AS booked_count,
                COUNT(DISTINCT CASE WHEN a.attendance_status='present' THEN a.id END) AS attended_count
            FROM meals m
            LEFT JOIN meal_booking mb ON m.id = mb.meal_id AND mb.status != 'cancelled'
            LEFT JOIN attendance  a  ON m.id = a.meal_id
            WHERE m.date >= ? AND m.date <= ?
            GROUP BY m.date, m.meal_type
            ORDER BY m.date DESC, m.meal_type
        ''', (start_date_str, end_date_str)).fetchall()
        conn.close()

        data = []
        total_booked   = 0
        total_attended = 0

        for r in rows:
            booked   = r['booked_count']   or 0
            attended = r['attended_count'] or 0
            wasted   = max(0, booked - attended)
            waste_pct = round((wasted / booked * 100) if booked > 0 else 0, 1)
            total_booked   += booked
            total_attended += attended
            data.append({
                'date':           r['date'],
                'meal_type':      r['meal_type'],
                'booked_count':   booked,
                'attended_count': attended,
                'wasted_count':   wasted,
                'waste_pct':      waste_pct,
            })

        overall_waste = max(0, total_booked - total_attended)
        overall_waste_pct = round((overall_waste / total_booked * 100) if total_booked > 0 else 0, 1)

        return jsonify({
            'success':             True,
            'start_date':          start_date_str,
            'end_date':            end_date_str,
            'records':             data,
            'summary': {
                'total_booked':    total_booked,
                'total_attended':  total_attended,
                'total_wasted':    overall_waste,
                'overall_waste_pct': overall_waste_pct,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/profile.html')
def profile_page():
    return render_template('profile.html')

@app.route('/<path:filename>')
def serve_html(filename):
    """Serve HTML files from root template folder"""
    if filename.endswith('.html'):
        return render_template(filename)
    from flask import abort
    abort(404)


# ==================== INITIALIZATION ====================

@app.route('/api/initdb', methods=['POST'])
def init_db():
    """Initialize database (first time setup)"""
    try:
        if init_database():
            return jsonify({'success': True, 'message': 'Database initialized successfully'})
        else:
            return jsonify({'success': False, 'message': 'Database initialization failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Always run migrations on startup
    init_database()
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])

