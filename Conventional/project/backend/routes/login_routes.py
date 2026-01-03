from flask import Flask, request, jsonify


from flask import request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from yourapp import app, db
from yourapp.models import User
from yourapp.schemas import UserSchema
from yourapp.utils import validate_input
from marshmallow.exceptions import ValidationError

@app.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and issue access token.

    :return: JSON response with access token and user role
    """
    try:
        # Validate input
        input_data = request.get_json()
        validate_input(input_data, required_fields=['username', 'password'])

        # Get user from database
        user = User.query.filter_by(username=input_data['username']).first()
        if not user:
            return jsonify({'msg': 'Invalid username or password'}), 401

        # Check password
        if not check_password_hash(user.password, input_data['password']):
            return jsonify({'msg': 'Invalid username or password'}), 401

        # Create access token
        access_token = create_access_token(identity=user.id)
        return jsonify({'token': access_token, 'role': user.role}), 200

    except ValidationError as err:
        return jsonify({'msg': 'Invalid input', 'errors': err.messages}), 400

    except Exception as err:
        db.session.rollback()
        return jsonify({'msg': 'Internal Server Error', 'error': str(err)}), 500
