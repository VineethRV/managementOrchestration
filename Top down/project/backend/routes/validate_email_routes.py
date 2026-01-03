
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# Create a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask Blueprint
attendance_blueprint = Blueprint('attendance_blueprint', __name__)

# Create a SQLAlchemy instance
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __init__(self, email, role):
        self.email = email
        self.role = role

# Define the route for validating email
@attendance_blueprint.route('/api/validate-email', methods=['GET'])
def validate_email():
    """
    Validate if an email is already in use.

    Request Body:
    {
        "email": "example@example.com"
    }

    Response:
    {
        "isAvailable": true,
        "message": "Email is available"
    }
    or
    {
        "isAvailable": false,
        "message": "Email is already in use"
    }
    """
    try:
        # Get the email from the request body
        data = request.json
        if not data:
            return jsonify({"isAvailable": False, "message": "Missing request body"}), 400

        email = data.get('email')
        if not email:
            return jsonify({"isAvailable": False, "message": "Missing email in request body"}), 400

        # Check if the email is already in use
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({"isAvailable": False, "message": "Email is already in use"}), 200
        else:
            return jsonify({"isAvailable": True, "message": "Email is available"}), 200

    except Exception as e:
        logger.error(f"Error validating email: {str(e)}")
        return jsonify({"isAvailable": False, "message": "Internal Server Error"}), 500

# Define a helper function to handle database transactions
def handle_database_transaction(func):
    def wrapper(*args, **kwargs):
        try:
            # Start a database transaction
            db.session.begin()
            result = func(*args, **kwargs)
            # Commit the transaction
            db.session.commit()
            return result
        except SQLAlchemyError as e:
            # Rollback the transaction
            db.session.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({"message": "Internal Server Error"}), 500
        except Exception as e:
            # Rollback the transaction
            db.session.rollback()
            logger.error(f"Error: {str(e)}")
            return jsonify({"message": "Internal Server Error"}), 500
    return wrapper
