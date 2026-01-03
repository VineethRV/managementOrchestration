from flask import Flask, request, jsonify


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Create a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a SQLite database engine
engine = create_engine('sqlite:///attendance.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the User model
class User(Base):
    """User model"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a Flask Blueprint
app = Blueprint('user_profile', __name__)

@app.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    Retrieve user profile details.

    Returns:
        A JSON response containing the user's profile details.

    Raises:
        401 Unauthorized: If the JWT token is invalid or missing.
        500 Internal Server Error: If an error occurs while retrieving the user's profile details.
    """
    try:
        # Get the user's identity from the JWT token
        user_id = get_jwt_identity()

        # Create a new session
        session = Session()

        # Query the user by their ID
        user = session.query(User).filter_by(id=user_id).first()

        # Check if the user exists
        if user is None:
            logger.error("User not found")
            return jsonify({"error": "User not found"}), 404

        # Return the user's profile details
        return jsonify({"profile_details": {"username": user.username, "role": user.role}}), 200

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error"}), 500



from flask import request, jsonify
from yourapp import app, db
from yourapp.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError, DataError
from marshmallow import Schema, fields, validates, ValidationError

class UserProfileSchema(Schema):
    """Schema for validating user profile update request."""
    username = fields.Str(required=True)
    role = fields.Str(required=True)

    @validates('role')
    def validate_role(self, value):
        """Validate role to ensure it's either STUDENT or TEACHER."""
        if value not in ['STUDENT', 'TEACHER']:
            raise ValidationError('Invalid role. Must be either STUDENT or TEACHER.')

@app.route('/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """
    Update user profile details.

    :return: JSON response with a message.
    """
    try:
        # Validate input using the schema
        schema = UserProfileSchema()
        data = schema.load(request.json)

        # Get the current user's ID from the JWT token
        current_user_id = get_jwt_identity()

        # Query the database for the user
        user = User.query.get(current_user_id)

        # If the user doesn't exist, return a 404
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Update the user's profile details
        user.username = data['username']
        user.role = data['role']

        # Commit the changes to the database
        db.session.commit()

        # Return a success message with a 200 status code
        return jsonify({'message': 'User profile updated successfully'}), 200

    except ValidationError as err:
        # If the input validation fails, return a 400 with the error message
        return jsonify({'message': 'Invalid request', 'errors': err.messages}), 400

    except IntegrityError:
        # If there's a database integrity error, return a 500
        return jsonify({'message': 'Database integrity error'}), 500

    except DataError:
        # If there's a database data error, return a 500
        return jsonify({'message': 'Database data error'}), 500

    except Exception as e:
        # Catch any other exceptions and return a 500
        return jsonify({'message': 'Internal server error'}), 500
