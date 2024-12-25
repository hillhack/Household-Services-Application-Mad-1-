from flask_sqlalchemy import SQLAlchemy
from app import db

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    # One-to-One relationship with Customer and Professional
    customer = db.relationship('Customer', backref='user', uselist=False, cascade='all, delete-orphan')
    professional = db.relationship('Professional', backref='user', uselist=False, cascade='all, delete-orphan')

# Customer Model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    contact_no = db.Column(db.String(15))  # Limits contact to phone number length
    address = db.Column(db.String(100))
    block = db.Column(db.String(10), default='NO')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship with ServiceRequest
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True, cascade='all, delete-orphan')

# Professional Model
class Professional(db.Model):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    address = db.Column(db.String(100))
    contact_no = db.Column(db.String(15))
    approved_status = db.Column(db.String(15), default='Pending')
    block = db.Column(db.String(10), default='NO')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships with Service and ServiceRequest
    services = db.relationship('Service', backref='professional', lazy=True, cascade='all, delete-orphan')
    service_requests = db.relationship('ServiceRequest', backref='professional', lazy=True, cascade='all, delete-orphan')

# Service Model
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    base_price = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.String(50))  # Years of experience
    description = db.Column(db.Text)

    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)

    # Relationship with ServiceRequest
    service_requests = db.relationship('ServiceRequest', backref='service', lazy=True, cascade='all, delete-orphan')

# ServiceRequest Model
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'))
    rating = db.Column(db.Integer)
    date_of_request = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime)
    service_status = db.Column(db.String(50), nullable=False)  # e.g., Pending, Completed
    review = db.Column(db.String(255))
