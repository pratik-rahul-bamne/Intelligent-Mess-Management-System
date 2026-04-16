-- =====================================================
-- Intelligent Mess Management System - Database Schema
-- =====================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('student', 'admin')) DEFAULT 'student',
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    roll_number TEXT,
    profile_photo TEXT,
    dietary_pref TEXT CHECK(dietary_pref IN ('veg', 'non-veg', 'any')) DEFAULT 'any',
    reset_token TEXT,
    reset_token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO users (username, email, password, role, name, status) VALUES
    ('admin', 'admin@mess.com', 'admin123', 'admin', 'Admin User', 'active'),
    ('student1', 'aayush@college.com', 'stud123', 'student', 'Aayush Singh', 'active'),
    ('student2', 'sneha@college.com', 'stud123', 'student', 'Sneha Verma', 'active');

-- Meals table
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    meal_type TEXT CHECK(meal_type IN ('breakfast', 'lunch', 'dinner')) NOT NULL,
    menu_items TEXT NOT NULL,
    price REAL DEFAULT 50.0,
    meal_tag TEXT CHECK(meal_tag IN ('veg', 'non-veg', 'mixed')) DEFAULT 'veg',
    capacity INTEGER DEFAULT 100,
    allergens TEXT DEFAULT '',
    booking_cutoff_hour INTEGER DEFAULT 8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO meals (date, meal_type, menu_items, price) VALUES
    ('2025-01-15', 'breakfast', 'Idli, Sambar, Tea', 30.0),
    ('2025-01-15', 'lunch', 'Rice, Dal, Sabji, Salad, Curd', 60.0),
    ('2025-01-15', 'dinner', 'Chapati, Paneer Curry, Rice, Gulab Jamun', 70.0),
    ('2025-01-16', 'breakfast', 'Poha, Tea, Banana', 30.0),
    ('2025-01-16', 'lunch', 'Rice, Dal, Aloo Sabji, Salad', 60.0),
    ('2025-01-16', 'dinner', 'Chapati, Chicken Curry, Rice, Sweet', 80.0);


-- Meal Booking table
CREATE TABLE IF NOT EXISTS meal_booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('booked', 'cancelled', 'completed')) DEFAULT 'booked',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE CASCADE,
    UNIQUE(user_id, meal_id)
);

INSERT OR IGNORE INTO meal_booking (user_id, meal_id, status) VALUES
    (2, 2, 'booked'),
    (2, 3, 'booked'),
    (3, 2, 'booked'),
    (3, 3, 'booked');

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_id INTEGER NOT NULL,
    attendance_status TEXT CHECK(attendance_status IN ('present', 'absent')) DEFAULT 'present',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qr_code TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO attendance (user_id, meal_id, attendance_status, timestamp) VALUES
    (2, 2, 'present', '2025-01-15 13:00:00'),
    (3, 2, 'present', '2025-01-15 13:15:00');

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    threshold REAL DEFAULT 10.0,
    last_updated DATE DEFAULT CURRENT_DATE,
    category TEXT DEFAULT 'general'
);

INSERT OR IGNORE INTO inventory (item_name, quantity, unit, threshold, last_updated, category) VALUES
    ('Rice', 120.5, 'kg', 20.0, '2025-01-15', 'grain'),
    ('Milk', 40.0, 'L', 10.0, '2025-01-15', 'dairy'),
    ('Wheat Flour', 80.0, 'kg', 15.0, '2025-01-15', 'grain'),
    ('Onions', 25.0, 'kg', 5.0, '2025-01-15', 'vegetable'),
    ('Tomatoes', 30.0, 'kg', 5.0, '2025-01-15', 'vegetable'),
    ('Oil', 50.0, 'L', 10.0, '2025-01-15', 'cooking');

-- Billing table
CREATE TABLE IF NOT EXISTS billing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    total_amount REAL NOT NULL DEFAULT 0.0,
    payment_status TEXT CHECK(payment_status IN ('Pending', 'Paid', 'Overdue')) DEFAULT 'Pending',
    payment_date DATE,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO billing (user_id, month, total_amount, payment_status, payment_date) VALUES
    (2, 'January 2025', 2200.0, 'Paid', '2025-01-15'),
    (3, 'January 2025', 2100.0, 'Pending', NULL);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_id INTEGER,
    message TEXT NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5) DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE SET NULL
);

INSERT OR IGNORE INTO feedback (user_id, meal_id, message, rating, created_at) VALUES
    (2, 2, 'Food was excellent today! Very tasty and fresh.', 5, '2025-01-15 14:00:00'),
    (3, 3, 'Milk was not fresh in the morning. Please improve quality.', 2, '2025-01-15 20:30:00');

-- Payment Transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bill_id INTEGER,
    amount REAL NOT NULL,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    status TEXT CHECK(status IN ('pending', 'success', 'failed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(bill_id) REFERENCES billing(id) ON DELETE SET NULL
);

-- Meal Ratings table (quick rating after attendance)
CREATE TABLE IF NOT EXISTS meal_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_id INTEGER NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE CASCADE,
    UNIQUE(user_id, meal_id)
);

-- Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO announcements (title, message, priority, created_by, created_at) VALUES
    ('Welcome to IMMS', 'Welcome to the Intelligent Mess Management System! Book your meals daily.', 'high', 1, CURRENT_TIMESTAMP);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT NOT NULL,
    type TEXT CHECK(type IN ('info', 'warning', 'success', 'danger')) DEFAULT 'info',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Audit Log table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Mess Settings table
CREATE TABLE IF NOT EXISTS mess_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO mess_settings (key, value, description) VALUES
    ('breakfast_price', '30.0', 'Default breakfast price in INR'),
    ('lunch_price', '60.0', 'Default lunch price in INR'),
    ('dinner_price', '70.0', 'Default dinner price in INR'),
    ('booking_cutoff_hour', '8', 'Hour before which breakfast booking must be done (24h format)'),
    ('mess_capacity', '200', 'Maximum students that can be served per meal'),
    ('mess_name', 'College Mess', 'Name of the mess'),
    ('overdue_days', '30', 'Days after which pending bill becomes overdue');

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    email TEXT,
    address TEXT,
    category TEXT DEFAULT 'general',
    status TEXT CHECK(status IN ('active', 'inactive')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO suppliers (name, contact, email, category) VALUES
    ('Fresh Grain Co.', '9876543210', 'freshgrain@example.com', 'grain'),
    ('Dairy Direct', '9123456780', 'dairy@example.com', 'dairy');
