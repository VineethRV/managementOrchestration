
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from yourapp import db
from yourapp.models import User

# Create a logger
logger = logging.getLogger(__name__)

# Define the blueprint
account_blueprint = Blueprint('account_blueprint', __name__)

# Define the User model (if it doesn't exist)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    loyalty_points = db.Column(db.Integer, default=0)
    reward_tier = db.Column(db.String(50), default='Basic')

# Define the route handlers
@account_blueprint.route('/api/account', methods=['GET'])
@jwt_required()
def get_account_information():
    """
    Retrieve user's account information.

    Returns:
        A JSON response with the user's account information.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'address': user.address
        }), 200
    except Exception as e:
        logger.error(f'Error: {e}')
        return jsonify({'message': 'Internal server error'}), 500

@account_blueprint.route('/api/account/loyalty', methods=['GET'])
@jwt_required()
def get_loyalty_points():
    """
    Retrieve user's loyalty or reward points.

    Returns:
        A JSON response with the user's loyalty points and reward tier.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        return jsonify({
            'loyalty_points': user.loyalty_points,
            'reward_tier': user.reward_tier
        }), 200
    except Exception as e:
        logger.error(f'Error: {e}')
        return jsonify({'message': 'Internal server error'}), 500

@account_blueprint.route('/api/account', methods=['PUT'])
@jwt_required()
def update_account_information():
    """
    Update user's account information.

    Request Body:
        - name (string)
        - email (string)
        - phone (string)
        - address (string)

    Returns:
        A JSON response with the updated user's account information.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        data = request.json
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
        db.session.commit()
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'address': user.address
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Email already exists'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error: {e}')
        return jsonify({'message': 'Internal server error'}), 500

@account_blueprint.route('/api/account/password', methods=['PUT'])
@jwt_required()
def update_password():
    """
    Update user's password.

    Request Body:
        - current_password (string)
        - new_password (string)
        - confirm_password (string)

    Returns:
        A JSON response with a success message.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        data = request.json
        if 'current_password' not in data or 'new_password' not in data or 'confirm_password' not in data:
            return jsonify({'message': 'Missing required fields'}), 400
        if data['new_password'] != data['confirm_password']:
            return jsonify({'message': 'Passwords do not match'}), 400
        if user.password != data['current_password']:
            return jsonify({'message': 'Current password is incorrect'}), 400
        user.password = data['new_password']
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error: {e}')
        return jsonify({'message': 'Internal server error'}), 500
