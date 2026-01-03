
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, DatabaseError
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from logging.handlers import RotatingFileHandler

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
logger.addHandler(handler)

# Initialize SQLAlchemy
db = SQLAlchemy()

# Models
class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    error_code = db.Column(db.String(100), unique=True, nullable=False)
    error_message = db.Column(db.String(200), nullable=False)
    error_stack = db.Column(db.String(500), nullable=False)
    reported = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Error('{self.error_code}', '{self.error_message}', '{self.error_stack}')"

# Routes
errors_blueprint = Blueprint('errors', __name__)

@errors_blueprint.route('/api/errors', methods=['POST'])
@jwt_required()
def log_error():
    """
    Log the error on the server-side for further investigation and debugging.

    Request Body:
    - error_code (string): unique error code or identifier
    - error_message (string): detailed error message
    - error_stack (string): error stack trace

    Returns:
    - error_id (integer): unique identifier for the logged error
    - message (string): success message
    """
    try:
        data = request.json
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        error_code = data.get('error_code')
        error_message = data.get('error_message')
        error_stack = data.get('error_stack')

        if not all([error_code, error_message, error_stack]):
            return jsonify({'message': 'Missing required fields'}), 400

        error = Error(error_code=error_code, error_message=error_message, error_stack=error_stack)
        db.session.add(error)
        db.session.commit()

        return jsonify({'error_id': error.id, 'message': 'Error logged successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Error with unique error code already exists'}), 400
    except DatabaseError as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return jsonify({'message': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'message': 'An error occurred'}), 500

@errors_blueprint.route('/api/errors/<int:error_id>', methods=['GET'])
@jwt_required()
def get_error_details(error_id):
    """
    Retrieve error details including a unique error code or identifier.

    Returns:
    - error_id (integer): unique identifier for the error
    - error_code (string): unique error code or identifier
    - error_message (string): detailed error message
    - error_stack (string): error stack trace
    - reported (boolean): whether the issue has been reported
    """
    try:
        error = Error.query.get(error_id)
        if not error:
            return jsonify({'message': 'Error not found'}), 404

        return jsonify({
            'error_id': error.id,
            'error_code': error.error_code,
            'error_message': error.error_message,
            'error_stack': error.error_stack,
            'reported': error.reported
        }), 200
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return jsonify({'message': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'message': 'An error occurred'}), 500

@errors_blueprint.route('/api/errors/<int:error_id>/report', methods=['POST'])
@jwt_required()
def report_issue(error_id):
    """
    Send a report of the issue to the system administrators.

    Request Body:
    - description (string): detailed description of the issue
    - steps_to_reproduce (string): steps to reproduce the issue

    Returns:
    - message (string): success message
    - reported (boolean): whether the issue has been reported
    """
    try:
        error = Error.query.get(error_id)
        if not error:
            return jsonify({'message': 'Error not found'}), 404

        data = request.json
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        description = data.get('description')
        steps_to_reproduce = data.get('steps_to_reproduce')

        if not all([description, steps_to_reproduce]):
            return jsonify({'message': 'Missing required fields'}), 400

        # Send report to system administrators (e.g., via email)
        # For demonstration purposes, this step is omitted

        error.reported = True
        db.session.commit()

        return jsonify({'message': 'Issue reported successfully', 'reported': True}), 200
    except DatabaseError as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return jsonify({'message': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'message': 'An error occurred'}), 500
