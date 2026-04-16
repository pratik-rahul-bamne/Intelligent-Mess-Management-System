# Intelligent Mess Management System

A comprehensive, full-stack web application for automating meal booking, billing, attendance, inventory management, and feedback collection in a college mess with AI-powered meal prediction.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login/signup with role-based access (Student/Admin)
- **Meal Booking**: Students can book meals for breakfast, lunch, and dinner
- **Attendance Tracking**: Digital attendance marking with QR code support
- **Billing & Payments**: Automated billing calculation and Razorpay payment gateway integration
- **Inventory Management**: Track inventory items with low stock alerts
- **Feedback System**: Submit feedback with ratings (1-5 stars)

### Advanced Features
- **AI/ML Meal Prediction**: Predicts daily meal requirements using Linear Regression
- **Automated Reports**: Generate PDF and Excel reports for analytics
- **Admin Dashboard**: Comprehensive analytics and management tools
- **Responsive Design**: Modern UI with Bootstrap styling

## 📋 System Requirements

- Python 3.7+
- SQLite3 (included with Python)
- Modern web browser (Chrome, Firefox, Edge)

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The database will be automatically initialized on first run. Alternatively, you can manually initialize:

```bash
python app.py
# Then visit http://localhost:5000/api/initdb (POST request)
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 4. Access the Application

- Open your browser and navigate to `http://localhost:5000`
- **Default Admin Credentials:**
  - Username: `admin`
  - Password: `admin123`
- **Default Student Credentials:**
  - Username: `student1`
  - Password: `stud123`

## 📊 Database Schema

### Entity Relationship Diagram Description

```
Users (1) ──< (N) Meal_Booking
Users (1) ──< (N) Attendance
Users (1) ──< (N) Billing
Users (1) ──< (N) Feedback
Meals (1) ──< (N) Meal_Booking
Meals (1) ──< (N) Attendance
Meals (1) ──< (N) Feedback
Billing (1) ──< (N) Payment_Transactions
```

### Tables

1. **users**: Stores user information (students and admins)
2. **meals**: Daily meal menu with date, type, and menu items
3. **meal_booking**: Records of meal bookings by users
4. **attendance**: Attendance records with timestamps and QR codes
5. **billing**: Monthly billing records with payment status
6. **inventory**: Inventory items with quantities and thresholds
7. **feedback**: User feedback with ratings
8. **payment_transactions**: Payment gateway transaction records

## 🔄 System Flow

### Meal Booking Flow
```
Student Login → View Meals → Book Meal → Mark Attendance → Generate Bill → Make Payment
```

### Attendance Flow
```
Book Meal → Generate QR Code (optional) → Scan/Mark Attendance → Update Booking Status
```

### Billing Flow
```
Calculate Monthly Bill → Create Razorpay Order → Process Payment → Verify Payment → Update Status
```

### ML Prediction Flow
```
Collect Historical Attendance Data → Train Linear Regression Model → Predict Tomorrow's Meal Count → Display Recommendations
```

## 🎯 API Endpoints

### Authentication
- `POST /api/signup` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/current_user` - Get current user info

### Meals
- `GET /api/meals` - Get all meals (with optional date filter)
- `POST /api/meals` - Create meal (Admin only)
- `PUT /api/meals/<id>` - Update meal (Admin only)
- `DELETE /api/meals/<id>` - Delete meal (Admin only)

### Bookings
- `GET /api/bookings` - Get bookings (filtered by user for students)
- `POST /api/bookings` - Book a meal
- `DELETE /api/bookings/<id>` - Cancel booking

### Attendance
- `GET /api/attendance` - Get attendance records
- `GET /api/attendance/qr/<meal_id>` - Generate QR code
- `POST /api/attendance` - Mark attendance

### Billing
- `GET /api/billing` - Get billing records
- `POST /api/billing/calculate` - Calculate bill for a month

### Payments
- `POST /api/payment/create_order` - Create Razorpay order
- `POST /api/payment/verify` - Verify payment signature

### Inventory
- `GET /api/inventory` - Get inventory items
- `POST /api/inventory` - Add item (Admin only)
- `PUT /api/inventory/<id>` - Update item (Admin only)
- `DELETE /api/inventory/<id>` - Delete item (Admin only)

### Feedback
- `GET /api/feedback` - Get feedback records
- `POST /api/feedback` - Submit feedback

### Analytics & Reports
- `GET /api/analytics/dashboard` - Dashboard statistics (Admin only)
- `GET /api/ml/predict_meals` - ML meal prediction (Admin only)
- `GET /api/reports/daily_meal_count` - Generate daily meal PDF
- `GET /api/reports/payment_report` - Generate payment Excel
- `GET /api/reports/inventory_usage` - Generate inventory chart

## 🤖 Machine Learning Module

The system uses **Linear Regression** to predict meal counts for the next day based on historical attendance data:

1. **Data Collection**: Collects last 30 days of attendance data
2. **Feature Engineering**: Uses day numbers as features and attendance counts as targets
3. **Model Training**: Trains a Linear Regression model
4. **Prediction**: Predicts meal counts by meal type (breakfast, lunch, dinner)
5. **Visualization**: Displays predictions with model accuracy score

### Usage
Navigate to Reports page → Click "Predict Meals" → View AI predictions

## 💳 Payment Gateway Integration

Razorpay sandbox integration for testing:

1. User initiates payment from billing page
2. System creates Razorpay order
3. User completes payment through Razorpay checkout
4. System verifies payment signature
5. Updates billing status to "Paid"

**Note**: Replace Razorpay keys in `config.py` with your sandbox keys for testing.

## 📄 Report Generation

### PDF Reports
- Daily meal count reports with date range filtering
- Generated using ReportLab library

### Excel Reports
- Payment reports with all transaction details
- Generated using pandas and openpyxl

### Charts
- Inventory status charts using matplotlib

## 🔒 Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control (RBAC)
- SQL injection prevention with parameterized queries
- CORS enabled for API security

## 📱 Frontend Structure

- **HTML Pages**: Modern, responsive templates
- **CSS**: Custom styling with gradient themes
- **JavaScript**: Vanilla JS for API integration
- **Razorpay SDK**: Integrated for payment processing

## 🧪 Testing

### Manual Testing Steps

1. **User Registration & Login**
   - Register a new user
   - Login with credentials
   - Test logout functionality

2. **Meal Booking**
   - View available meals
   - Book a meal
   - Cancel a booking

3. **Attendance**
   - Mark attendance for a booked meal
   - Generate QR code (optional)

4. **Billing**
   - Calculate monthly bill
   - Initiate payment (test mode)
   - Verify payment

5. **Inventory (Admin)**
   - Add inventory items
   - Update quantities
   - Check low stock alerts

6. **Reports (Admin)**
   - Generate PDF reports
   - Generate Excel reports
   - Run ML predictions

## 📦 Project Structure

```
PRATHAM CREATION/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── mess_management_schema.sql  # Database schema
├── README.md                   # This file
├── index.html                  # Login page
├── signup.html                 # Registration page
├── dashboard.html              # Dashboard
├── meals.html                  # Meal booking
├── attendance.html             # Attendance management
├── billing.html                # Billing & payments
├── inventory.html              # Inventory management
├── feedback.html               # Feedback system
├── users.html                  # User management (Admin)
├── reports.html                # Reports & analytics (Admin)
├── settings.html               # System settings
└── assets/
    ├── css/
    │   └── styles.css          # Styling
    └── js/
        └── main.js             # JavaScript logic
```

## 🚀 Deployment

### Local Deployment
1. Ensure all dependencies are installed
2. Run `python app.py`
3. Access at `http://localhost:5000`

### Production Deployment
1. Set `DEBUG = False` in `config.py`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure a reverse proxy (Nginx)
4. Set up SSL certificate
5. Update Razorpay keys to production keys

### Cloud Deployment Options
- **Render**: Deploy Flask app with PostgreSQL
- **PythonAnywhere**: Direct Python hosting
- **Heroku**: Platform-as-a-Service deployment
- **AWS/GCP/Azure**: Full cloud infrastructure

## 🐛 Troubleshooting

### Database Issues
- Delete `mess_management.db` and reinitialize
- Check SQLite3 installation

### Payment Gateway Issues
- Verify Razorpay sandbox keys in `config.py`
- Check Razorpay checkout script is loaded

### ML Prediction Issues
- Ensure at least 7 days of historical data
- Check scikit-learn installation

## 📝 Future Enhancements

- [ ] Real-time notifications
- [ ] Email alerts for low stock
- [ ] SMS reminders for meal bookings
- [ ] Advanced ML models (Random Forest, XGBoost)
- [ ] Mobile app development
- [ ] Multi-mess support
- [ ] Advanced analytics dashboard
- [ ] Integration with college ERP systems

## 👥 Contributing

This is a project for educational purposes. Feel free to fork and enhance!

## 📄 License

This project is open source and available for educational use.

## 📞 Support

For issues or questions, please refer to the documentation or contact the development team.

---

**Developed with ❤️ for efficient mess management**

