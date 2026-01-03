from flask import Flask, request, jsonify


from flask import request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from yourapp import app, db
from yourapp.models import User
from yourapp.schemas import UserSchema
from yourapp.utils import validate_input

@app.route('/auth/register', methods=['POST'])
def register_user():
    """
    Register new user and issue access token.

    :return: JSON response with access token and user role
    """
    try:
        # Get request body
        data = request.get_json()

        # Validate input
        errors = validate_input(data, ['username', 'password', 'role'])
        if errors:
            return jsonify({'errors': errors}), 400

        # Validate role
        if data['role'] not in ['STUDENT', 'TEACHER']:
            return jsonify({'error': 'Invalid role'}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400

        # Create new user
        new_user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role=data['role']
        )

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=new_user.id)

        # Return response
        return jsonify({
            'token': access_token,
            'role': new_user.role
        }), 201

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': str(e)}), 500
