# Intelligent Mess Management System - System Design Document

## 1. System Overview

The Intelligent Mess Management System is a web-based application designed to automate and streamline all operations of a college mess, including meal booking, attendance tracking, billing, inventory management, and feedback collection. The system incorporates AI/ML capabilities to predict meal requirements and minimize food wastage.

## 2. System Architecture

### 2.1 Three-Tier Architecture

```
┌─────────────────────────────────────┐
│         Presentation Layer           │
│    (HTML, CSS, JavaScript)          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Application Layer              │
│      (Flask REST API)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Data Layer                    │
│      (SQLite Database)               │
└─────────────────────────────────────┘
```

### 2.2 Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Database**: SQLite3 (can be migrated to MySQL/PostgreSQL)
- **Payment Gateway**: Razorpay
- **ML Framework**: scikit-learn (Linear Regression)
- **Reporting**: ReportLab (PDF), Pandas/OpenPyXL (Excel), Matplotlib (Charts)

## 3. Database Design

### 3.1 Entity Relationship Diagram (Textual Representation)

```
┌─────────────┐
│    Users    │
│─────────────│
│ id (PK)     │
│ username    │
│ email       │
│ password    │
│ role        │
│ name        │
│ status      │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────┐      ┌─────────────┐
│  Meal_Booking   │──────│    Meals    │
│─────────────────│ N:1   │─────────────│
│ id (PK)         │      │ id (PK)     │
│ user_id (FK)    │      │ date        │
│ meal_id (FK)    │      │ meal_type   │
│ status          │      │ menu_items  │
│ booking_date    │      │ price       │
└──────┬──────────┘      └─────────────┘
       │
       │ 1:1
       │
┌──────▼──────────┐
│   Attendance    │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ meal_id (FK)    │
│ status          │
│ timestamp       │
│ qr_code         │
└─────────────────┘

┌─────────────┐      ┌──────────────────┐
│    Users    │──────│     Billing      │
│─────────────│ 1:N  │──────────────────│
│             │      │ id (PK)          │
└─────────────┘      │ user_id (FK)     │
                     │ month            │
                     │ total_amount     │
                     │ payment_status   │
                     │ payment_date     │
                     └────────┬─────────┘
                              │
                              │ 1:N
                              │
                    ┌─────────▼───────────┐
                    │ Payment_Transactions│
                    │─────────────────────│
                    │ id (PK)             │
                    │ bill_id (FK)        │
                    │ razorpay_order_id   │
                    │ razorpay_payment_id │
                    │ status              │
                    └─────────────────────┘

┌─────────────┐      ┌─────────────┐
│    Users    │──────│  Feedback   │
│─────────────│ 1:N  │─────────────│
│             │      │ id (PK)     │
└─────────────┘      │ user_id (FK)│
                     │ meal_id(FK) │
                     │ message     │
                     │ rating      │
                     │ created_at  │
                     └─────────────┘

┌─────────────┐
│  Inventory  │
│─────────────│
│ id (PK)     │
│ item_name   │
│ quantity    │
│ unit        │
│ threshold   │
│ category    │
│ last_updated│
└─────────────┘
```

### 3.2 Table Descriptions

#### Users Table
- Stores all system users (students and administrators)
- Role-based access control
- Password hashed using Werkzeug

#### Meals Table
- Daily meal menu entries
- Supports breakfast, lunch, dinner
- Includes menu items and pricing

#### Meal_Booking Table
- Links users to meals they've booked
- Tracks booking status (booked, cancelled, completed)

#### Attendance Table
- Records actual meal attendance
- Supports QR code-based check-in
- Timestamp for audit trail

#### Billing Table
- Monthly billing records per user
- Payment status tracking
- Integration with payment gateway

#### Payment_Transactions Table
- Records all payment gateway transactions
- Stores Razorpay order and payment IDs
- Payment verification status

#### Inventory Table
- Tracks mess inventory items
- Low stock threshold alerts
- Category-based organization

#### Feedback Table
- User feedback with ratings (1-5 stars)
- Optional meal-specific feedback
- Timestamped records

## 4. System Workflows

### 4.1 Meal Booking Workflow

```
┌──────────┐
│ Student  │
│  Login   │
└────┬─────┘
     │
     ▼
┌─────────────┐
│ View Meals  │
└────┬────────┘
     │
     ▼
┌─────────────┐      ┌──────────────┐
│ Select Meal│──────│Check Capacity│
└────┬────────┘      └──────┬───────┘
     │                      │
     ▼                      │
┌─────────────┐             │
│ Book Meal   │◄────────────┘
└────┬────────┘
     │
     ▼
┌─────────────┐
│Confirmation │
└─────────────┘
```

### 4.2 Attendance Workflow

```
┌──────────────┐
│ Booked Meal  │
└──────┬───────┘
       │
       ├─────────► Generate QR Code (Optional)
       │
       ▼
┌──────────────┐
│ Mark Attendance│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Update Booking│
│  Status      │
└──────────────┘
```

### 4.3 Billing & Payment Workflow

```
┌──────────────┐
│Calculate Bill│
│  (Monthly)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Create Bill  │
│   Record     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Create Razorpay│
│    Order     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│User Payment  │
│  Processing  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Verify Payment│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Update Status │
└──────────────┘
```

### 4.4 ML Prediction Workflow

```
┌──────────────────┐
│ Collect Historical│
│  Attendance Data  │
│   (Last 30 days)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Feature Engineering│
│  (Day numbers)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Train Model      │
│ (Linear Regression)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Predict Tomorrow │
│    Meal Count    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Display Results  │
│   & Accuracy     │
└──────────────────┘
```

## 5. Security Design

### 5.1 Authentication
- Password hashing using Werkzeug (PBKDF2)
- Session-based authentication
- Session timeout handling

### 5.2 Authorization
- Role-based access control (RBAC)
- Student role: Limited access
- Admin role: Full system access

### 5.3 Data Protection
- SQL injection prevention (parameterized queries)
- XSS protection (input sanitization)
- CORS configuration
- Secure payment gateway integration

## 6. AI/ML Module Design

### 6.1 Prediction Model
- **Algorithm**: Linear Regression
- **Features**: Day numbers (temporal feature)
- **Target**: Daily meal attendance count
- **Training Data**: Last 30 days of attendance
- **Output**: Predicted meal counts by meal type

### 6.2 Model Training Process
1. Query historical attendance data
2. Aggregate by date and meal type
3. Convert dates to numerical day numbers
4. Train Linear Regression model
5. Predict next day's meal count
6. Calculate model accuracy (R² score)

### 6.3 Future Enhancements
- Random Forest for better accuracy
- Time series analysis (ARIMA)
- External factors (holidays, events)
- Multi-variate regression

## 7. Reporting System

### 7.1 PDF Reports
- **Library**: ReportLab
- **Content**: Daily meal counts, attendance summaries
- **Features**: Date range filtering, table formatting

### 7.2 Excel Reports
- **Library**: Pandas + OpenPyXL
- **Content**: Payment reports, billing summaries
- **Features**: Auto-column width, formatted tables

### 7.3 Charts & Visualizations
- **Library**: Matplotlib
- **Content**: Inventory status, usage trends
- **Format**: PNG images

## 8. Integration Points

### 8.1 Payment Gateway (Razorpay)
- Order creation API
- Payment verification API
- Webhook support (future)
- Sandbox mode for testing

### 8.2 QR Code Generation
- Library: qrcode + Pillow
- Data format: `user_id:meal_id:timestamp`
- Base64 encoding for web display

## 9. Deployment Architecture

### 9.1 Development Setup
```
Local Machine
├── Flask Development Server
├── SQLite Database
└── Browser Testing
```

### 9.2 Production Setup
```
Load Balancer
    │
    ├─── App Server 1 (Gunicorn)
    ├─── App Server 2 (Gunicorn)
    │
    ├─── Database Server (PostgreSQL)
    │
    └─── Static File Server (Nginx)
```

## 10. Performance Considerations

- Database indexing on foreign keys
- Query optimization for large datasets
- Caching for frequently accessed data
- Pagination for large result sets
- Asynchronous payment processing

## 11. Scalability

- Horizontal scaling with load balancer
- Database connection pooling
- Stateless API design
- CDN for static assets
- Microservices architecture (future)

## 12. Error Handling

- Try-catch blocks in all API endpoints
- Meaningful error messages
- Logging for debugging
- User-friendly error pages
- Graceful degradation

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-15

