from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import logging

# ... rest of the code ...
app = Flask(__name__)

# Route for Home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for Booking page
@app.route('/booking')
def booking():
    return render_template('booking.html')

# Route for About Us page
@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

# Route for Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route for Account Info page
@app.route('/account_info')
def account_info():
    return render_template('account_info.html')

# Route for Booking Schedule page
@app.route('/booking_schedule')
def booking_schedule():
    return render_template('booking_schedule.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
