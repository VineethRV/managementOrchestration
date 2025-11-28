
# Import necessary libraries
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from sqlalchemy.exc import IntegrityError
import logging

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define SQLAlchemy models
class User(db.Model):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Create all tables in the engine
with app.app_context():
    db.create_all()

# Define a function to validate request data
def validate_request_data(data):
    """Validate request data"""
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    return True, ""

# Define a function to create a new user
def create_user(data):
    """Create a new user"""
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Error creating user: {e}")
        return None

# Define the route for creating a new user account
@app.route('/api/create-account', methods=['POST'])
def create_account():
    """
    Create a new user account

    Request Body:
        - username (string, required): Unique username chosen by the user
        - email (string, required): Unique email address of the user
        - password (string, required): Password for the user account
        - first_name (string, optional): First name of the user
        - last_name (string, optional): Last name of the user

    Response:
        - user_id (integer): Unique identifier for the newly created user account
        - username (string): Username chosen by the user
        - email (string): Email address of the user
        - token (string): Authentication token for the user
    """
    try:
        data = request.json
        is_valid, error_message = validate_request_data(data)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        user = create_user(data)
        if user is None:
            return jsonify({"error": "Failed to create user"}), 500

        token = create_access_token(identity=user.id)
        return jsonify({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "token": token
        }), 201
    except Exception as e:
        logging.error(f"Error creating user account: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
