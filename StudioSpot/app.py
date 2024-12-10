from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
app.config['UPLOAD_FOLDER'] = 'static/images'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the uploaded file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Test the database connection
def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Your MySQL password
            database='celestial'
        )
        if conn.is_connected():
            logging.info("Database connection successful.")
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to the database: {e}")
    finally:
        if conn.is_connected():
            conn.close()

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="celestial"
        )
        return connection
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

# Retrieve all products
def get_all_products():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return products
    else:
        return []

@app.route('/')
def home():
    return render_template('home.html')






if __name__ == '__main__':
    app.run(debug=True)
