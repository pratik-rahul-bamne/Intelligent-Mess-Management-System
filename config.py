# config.py - Configuration file for Mess Management System
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production-2024'
    
    # Database Configuration
    DATABASE = 'mess_management.db'
    
    # Razorpay Configuration (Sandbox - Replace with your keys)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID') or 'rzp_test_1DP5mmOlF5G5ag'
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET') or 'test_secret_key_replace'
    
    # Application Settings
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # Meal Prices (default)
    MEAL_PRICES = {
        'breakfast': 30.0,
        'lunch': 60.0,
        'dinner': 70.0
    }

