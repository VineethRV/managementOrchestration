
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, DataError
from werkzeug.security import generate_password_hash
import jwt
import logging
from datetime import datetime, timedelta

# Create a logger
logger = logging.getLogger(__name__)

# Create a Flask Blueprint
password_recovery_blueprint = Blueprint('password_recovery', __name__)

# Create a SQLAlchemy instance
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    password_recovery_token = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Define the PasswordRecoveryToken model
class PasswordRecoveryToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"PasswordRecoveryToken('{self.token}', '{self.expires_at}')"

# Helper function to generate a password recovery token
def generate_password_recovery_token(user_id):
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }, 'secret_key', algorithm='HS256')
    return token

# Helper function to validate a password recovery token
def validate_password_recovery_token(token):
    try:
        payload = jwt.decode(token, 'secret_key', algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Route to send a password recovery email
@password_recovery_blueprint.route('/api/password-recovery/send-email', methods=['POST'])
def send_password_recovery_email():
    """
    Sends a password recovery email to the user.

    Request Body:
        - username_or_email (string): The username or email address of the user.
        - client_url (string): The URL of the client application to redirect the user after password recovery.

    Response:
        - success (boolean): Indicates whether the password recovery email was sent successfully.
        - message (string): A message describing the result of the operation.
        - token (string): The password recovery token.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        username_or_email = data.get('username_or_email')
        client_url = data.get('client_url')

        if not username_or_email or not client_url:
            return jsonify({'success': False, 'message': 'Username or email and client URL are required'}), 400

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        token = generate_password_recovery_token(user.id)
        user.password_recovery_token = token

        db.session.add(user)
        db.session.commit()

        # Send the password recovery email
        # ...

        return jsonify({'success': True, 'message': 'Password recovery email sent successfully', 'token': token}), 200
    except Exception as e:
        logger.error(f"Error sending password recovery email: {str(e)}")
        return jsonify({'success': False, 'message': 'Error sending password recovery email'}), 500

# Route to validate a username or email
@password_recovery_blueprint.route('/api/password-recovery/validate-credentials', methods=['POST'])
def validate_credentials():
    """
    Validates if the username or email address exists in the database.

    Request Body:
        - username_or_email (string): The username or email address to validate.

    Response:
        - valid (boolean): Indicates whether the username or email address exists in the database.
        - message (string): A message describing the result of the operation.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'valid': False, 'message': 'Invalid request data'}), 400

        username_or_email = data.get('username_or_email')

        if not username_or_email:
            return jsonify({'valid': False, 'message': 'Username or email is required'}), 400

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user:
            return jsonify({'valid': True, 'message': 'Username or email is valid'}), 200
        else:
            return jsonify({'valid': False, 'message': 'Username or email is not valid'}), 404
    except Exception as e:
        logger.error(f"Error validating username or email: {str(e)}")
        return jsonify({'valid': False, 'message': 'Error validating username or email'}), 500

# Route to resend a password recovery email
@password_recovery_blueprint.route('/api/password-recovery/resend-email', methods=['POST'])
def resend_password_recovery_email():
    """
    Resends the password recovery email if the user does not receive it.

    Request Body:
        - username_or_email (string): The username or email address of the user.
        - client_url (string): The URL of the client application to redirect the user after password recovery.

    Response:
        - success (boolean): Indicates whether the password recovery email was resent successfully.
        - message (string): A message describing the result of the operation.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        username_or_email = data.get('username_or_email')
        client_url = data.get('client_url')

        if not username_or_email or not client_url:
            return jsonify({'success': False, 'message': 'Username or email and client URL are required'}), 400

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        token = generate_password_recovery_token(user.id)
        user.password_recovery_token = token

        db.session.add(user)
        db.session.commit()

        # Send the password recovery email
        # ...

        return jsonify({'success': True, 'message': 'Password recovery email resent successfully'}), 200
    except Exception as e:
        logger.error(f"Error resending password recovery email: {str(e)}")
        return jsonify({'success': False, 'message': 'Error resending password recovery email'}), 500

# Route to reset a password
@password_recovery_blueprint.route('/api/password-recovery/reset-password', methods=['PUT'])
def reset_password():
    """
    Resets the user's password.

    Request Body:
        - token (string): The password recovery token.
        - new_password (string): The new password for the user.
        - confirm_password (string): The confirmation of the new password.

    Response:
        - success (boolean): Indicates whether the password was reset successfully.
        - message (string): A message describing the result of the operation.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        token = data.get('token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not token or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'Token, new password, and confirm password are required'}), 400

        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New password and confirm password do not match'}), 400

        user_id = validate_password_recovery_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': 'Invalid password recovery token'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        user.password = generate_password_hash(new_password)
        user.password_recovery_token = None

        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return jsonify({'success': False, 'message': 'Error resetting password'}), 500

# Route to verify a password recovery token
@password_recovery_blueprint.route('/api/password-recovery/verify-token', methods=['GET'])
def verify_password_recovery_token():
    """
    Verifies the password recovery token sent in the email.

    Request Body:
        - token (string): The password recovery token.

    Response:
        - valid (boolean): Indicates whether the password recovery token is valid.
        - message (string): A message describing the result of the operation.
        - user_id (integer): The ID of the user associated with the token.
    """
    try:
        token = request.args.get('token')

        if not token:
            return jsonify({'valid': False, 'message': 'Token is required'}), 400

        user_id = validate_password_recovery_token(token)
        if not user_id:
            return jsonify({'valid': False, 'message': 'Invalid password recovery token'}), 400

        return jsonify({'valid': True, 'message': 'Password recovery token is valid', 'user_id': user_id}), 200
    except Exception as e:
        logger.error(f"Error verifying password recovery token: {str(e)}")
        return jsonify({'valid': False, 'message': 'Error verifying password recovery token'}), 500
