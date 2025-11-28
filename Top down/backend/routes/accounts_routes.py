
# Models
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import logging

db = SQLAlchemy()

class Account(db.Model):
    """User account model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    def __init__(self, name, email, password, phone=None):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.phone = phone

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Routes
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from marshmallow import Schema, fields, validates, ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
db.init_app(app)
jwt = JWTManager(app)

class AccountSchema(Schema):
    """Account schema for validation"""
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    phone = fields.Str()

    @validates('email')
    def validate_email(self, value):
        if Account.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')

# Helper function to handle errors
def handle_error(error):
    logging.error(error)
    return jsonify({'error': str(error)}), 500

# Create Account endpoint
@app.route('/api/accounts', methods=['POST'])
def create_account():
    """
    Create a new user account.

    :return: JSON response with account details
    """
    try:
        schema = AccountSchema()
        data = request.get_json()
        errors = schema.validate(data)
        if errors:
            return jsonify({'error': 'Invalid request data', 'details': errors}), 400

        account = Account(data['name'], data['email'], data['password'], data.get('phone'))
        db.session.add(account)
        db.session.commit()

        return jsonify({
            'id': account.id,
            'name': account.name,
            'email': account.email,
            'phone': account.phone
        }), 201
    except Exception as e:
        db.session.rollback()
        return handle_error(e)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
