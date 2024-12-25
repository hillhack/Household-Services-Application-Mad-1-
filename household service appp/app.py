from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import csv

app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models and routes
from models import User, Customer, Professional, Service, ServiceRequest
from routes import main
app.register_blueprint(main)


# Function to create an admin user if it doesn't already exist
def create_admin():
    admin_exists = User.query.filter_by(email='admin@gmail.com').first()
    print(admin_exists)

    if not admin_exists:
        admin = User(
            username='Admin',
            email='admin@gmail.com',
            password=generate_password_hash('admin', method='pbkdf2:sha256'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user with this email already exists.")



# Run the setup to create tables and populate data
with app.app_context():
    db.create_all()  # Ensures tables are created
    create_admin()


