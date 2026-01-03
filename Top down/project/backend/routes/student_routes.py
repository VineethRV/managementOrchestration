
# Models (if needed)
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import logging

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"Student('{self.name}', '{self.email}', '{self.role}')"

# Routes
from flask import Blueprint, request, jsonify
from functools import wraps
import datetime

student_blueprint = Blueprint('student', __name__)

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_student = Student.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_student, *args, **kwargs)
    return decorated

# Get Student Details
@student_blueprint.route('/api/student/details', methods=['GET'])
@token_required
def get_student_details(current_student):
    """
    Retrieve student details to confirm identity.

    :param current_student: The current student object
    :return: A JSON response with the student's details
    """
    try:
        student_details = {
            'student_id': current_student.id,
            'name': current_student.name,
            'email': current_student.email,
            'role': current_student.role
        }
        return jsonify(student_details), 200
    except Exception as e:
        logging.error(f"Error getting student details: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Error handler
@student_blueprint.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

@student_blueprint.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal Server Error'}), 500
