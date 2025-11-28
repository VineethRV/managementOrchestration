
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# Set up logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Routes
@app.route('/api/registration/form', methods=['GET'])
def get_registration_form():
    """
    Returns the registration form with fields for username, email, password, and confirm password.
    """
    return jsonify({
        'fields': [
            {'name': 'username', 'type': 'text', 'description': 'Username input field'},
            {'name': 'email', 'type': 'email', 'description': 'Email input field'},
            {'name': 'password', 'type': 'password', 'description': 'Password input field'},
            {'name': 'confirmPassword', 'type': 'password', 'description': 'Confirm password input field'}
        ]
    }), 200

@app.route('/api/registration/validate', methods=['POST'])
def validate_registration_form():
    """
    Validates the registration form data, including email format and password strength.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if not username or not email or not password or not confirm_password:
            return jsonify({'error': 'All fields are required'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        # Basic email validation
        if '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400

        # Basic password strength validation
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400

        return jsonify({'valid': True, 'errors': {}}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/registration/username/<string:username>', methods=['GET'])
def check_username_availability(username):
    """
    Checks if a username is available and not already in use.
    """
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'available': False, 'message': 'Username is already taken'}), 200
        return jsonify({'available': True, 'message': 'Username is available'}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/registration/email/<string:email>', methods=['GET'])
def check_email_availability(email):
    """
    Checks if an email is available and not already in use.
    """
    try:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'available': False, 'message': 'Email is already taken'}), 200
        return jsonify({'available': True, 'message': 'Email is available'}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/registration', methods=['POST'])
def create_new_user():
    """
    Creates a new user account with the provided registration form data.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if not username or not email or not password or not confirm_password:
            return jsonify({'error': 'All fields are required'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'error': 'Username is already taken'}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'error': 'Email is already taken'}), 400

        new_user = User(username, email, password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'userId': new_user.id, 'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
