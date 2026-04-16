# Quick Start Guide - Intelligent Mess Management System

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python app.py
```

The server will start at `http://localhost:5000`

### Step 3: Access the System

1. Open browser: `http://localhost:5000`
2. **Login as Admin:**
   - Username: `admin`
   - Password: `admin123`

3. **Login as Student:**
   - Username: `student1`
   - Password: `stud123`

## 📋 Quick Test Checklist

### For Students:
- [ ] Login successfully
- [ ] View available meals
- [ ] Book a meal
- [ ] Mark attendance
- [ ] View billing
- [ ] Submit feedback

### For Admin:
- [ ] View dashboard analytics
- [ ] Create/edit meals
- [ ] Manage inventory
- [ ] Generate reports
- [ ] Run ML prediction
- [ ] View all users

## 💡 Key Features to Test

### 1. Meal Booking
- Navigate to "Meals" page
- Click "Book" on any meal
- Verify booking appears in dashboard

### 2. Attendance
- Go to "Attendance" page
- Enter meal ID and mark attendance
- Check attendance records

### 3. Payment (Test Mode)
- Go to "Billing" page
- Calculate bill for a month
- Click "Pay Now"
- Use Razorpay test card: `4111 1111 1111 1111`
- CVV: Any 3 digits
- Expiry: Any future date

### 4. ML Prediction
- Navigate to "Reports" page (Admin only)
- Click "Predict Meals"
- View AI predictions

### 5. Generate Reports
- Go to "Reports" page
- Generate PDF report
- Generate Excel report
- View inventory chart

## 🔧 Configuration

### Razorpay Setup (Optional)
1. Sign up at https://razorpay.com
2. Get sandbox API keys
3. Update `config.py`:
   ```python
   RAZORPAY_KEY_ID = 'your_key_id'
   RAZORPAY_KEY_SECRET = 'your_key_secret'
   ```

## 🐛 Common Issues

### Database Not Found
- Delete `mess_management.db` if exists
- Restart application (auto-initializes)

### Module Not Found
- Ensure all dependencies installed: `pip install -r requirements.txt`

### Port Already in Use
- Change port in `config.py`: `PORT = 5001`
- Or kill process using port 5000

### Payment Gateway Error
- Check Razorpay keys in `config.py`
- Ensure Razorpay checkout script is loaded

## 📱 Browser Compatibility

- Chrome (Recommended)
- Firefox
- Edge
- Safari

## 🎯 Next Steps

1. Create more users via signup page
2. Add more meals for testing
3. Generate various reports
4. Test ML predictions with historical data
5. Explore all admin features

## 📞 Need Help?

Refer to:
- `README.md` - Full documentation
- `SYSTEM_DESIGN.md` - Architecture details
- Code comments in `app.py` for API details

---

**Happy Testing! 🎉**

