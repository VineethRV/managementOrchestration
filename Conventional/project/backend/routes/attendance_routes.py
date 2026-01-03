from flask import Flask, request, jsonify


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, Unauthorized, InternalServerError

# Create a SQLite database engine
engine = create_engine('sqlite:///attendance.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the StudentAttendance model
class StudentAttendance(Base):
    __tablename__ = 'student_attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    attendance_date = Column(Integer)
    is_present = Column(Integer)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a new Blueprint
app = Blueprint('attendance', __name__)

# Define the route handler
@app.route('/student/attendance/summary', methods=['GET'])
@jwt_required()
def get_student_attendance_summary():
    """
    Retrieve student attendance summary.

    Returns:
        A JSON response containing the attendance summary.
    """
    try:
        # Get the student ID from the JWT token
        student_id = get_jwt_identity()

        # Create a new session
        session = Session()

        # Query the database for the student's attendance records
        attendance_records = session.query(StudentAttendance).filter_by(student_id=student_id).all()

        # Calculate the attendance summary
        total_days = len(attendance_records)
        present_days = sum(1 for record in attendance_records if record.is_present)
        absent_days = total_days - present_days

        # Create the attendance summary response
        attendance_summary = {
            'attendance_summary': {
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days
            }
        }

        # Return the attendance summary response
        return jsonify(attendance_summary), 200

    except SQLAlchemyError as e:
        # Handle database errors
        return jsonify({'error': 'Database error'}), 500

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': 'Unexpected error'}), 500

    finally:
        # Close the session
        session.close()



from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a SQLAlchemy engine
engine = create_engine('sqlite:///attendance.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the Attendance model
class Attendance(Base):
    """Attendance model"""
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)

# Create all tables in the engine
Base.metadata.create_all(engine)

@app.route('/student/attendance/history', methods=['GET'])
@jwt_required
def get_student_attendance_history():
    """
    Retrieve student attendance history.

    Returns:
        A JSON response containing the attendance history of the student.

    Raises:
        401: If the JWT token is invalid or missing.
        403: If the user is not a student.
        500: If an internal server error occurs.
    """
    try:
        # Get the student ID from the JWT token
        student_id = get_jwt_identity()

        # Check if the user is a student
        if not is_student(student_id):
            logger.error("User is not a student")
            return jsonify({"msg": "Forbidden"}), 403

        # Create a new session
        session = Session()

        # Query the attendance history for the student
        attendance_history = session.query(Attendance).filter_by(student_id=student_id).all()

        # Convert the attendance history to a JSON response
        response = []
        for attendance in attendance_history:
            response.append({
                "date": attendance.date.strftime("%Y-%m-%d"),
                "status": attendance.status
            })

        # Close the session
        session.close()

        # Return the attendance history
        return jsonify({"attendance_history": response}), 200

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500


def is_student(student_id):
    """
    Check if the user is a student.

    Args:
        student_id (int): The ID of the user.

    Returns:
        bool: True if the user is a student, False otherwise.
    """
    # For simplicity, this function assumes that the user is a student if their ID is even.
    # In a real-world application, this function would query the database to check the user's role.
    return student_id % 2 == 0



from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from yourapp import app, db
from yourapp.models import Student, Attendance

@app.route('/student/attendance/mark', methods=['POST'])
@jwt_required()
def mark_student_attendance():
    """
    Marks student attendance for the day.

    :return: A JSON response with a message.
    """
    try:
        # Get the current user's identity
        current_user = get_jwt_identity()

        # Check if the user is a student
        student = Student.query.filter_by(username=current_user).first()
        if not student:
            return jsonify({"message": "You are not a student."}), 403

        # Mark attendance for the student
        attendance = Attendance(student_id=student.id, date=datetime.date.today())
        db.session.add(attendance)
        db.session.commit()

        return jsonify({"message": "Attendance marked successfully."}), 201

    except SQLAlchemyError as e:
        # Handle database errors
        db.session.rollback()
        return jsonify({"message": "An error occurred while marking attendance."}), 500

    except Exception as e:
        # Handle any other errors
        return jsonify({"message": "An error occurred."}), 500



from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Create a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask Blueprint
app = Blueprint('attendance', __name__)

# Create a database engine
engine = create_engine('sqlite:///attendance.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the Attendance model
class Attendance(Base):
    """Attendance model"""
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    date = Column(String)
    status = Column(String)

    def __repr__(self):
        return f'Attendance(student_id={self.student_id}, date={self.date}, status={self.status})'

# Create all tables in the engine
Base.metadata.create_all(engine)

@app.route('/teacher/attendance', methods=['GET'])
@jwt_required()
def get_teacher_attendance():
    """
    Retrieve teacher attendance records

    Returns:
        A JSON response containing the attendance records
    """
    try:
        # Get the teacher's identity from the JWT token
        teacher_id = get_jwt_identity()

        # Create a new session
        session = Session()

        # Query the attendance records
        attendance_records = session.query(Attendance).all()

        # Convert the attendance records to a list of dictionaries
        attendance_list = []
        for record in attendance_records:
            attendance_list.append({
                'student_id': record.student_id,
                'date': record.date,
                'status': record.status
            })

        # Return the attendance records as a JSON response
        return jsonify({'attendance_records': attendance_list}), 200

    except Exception as e:
        # Log the error and return a 500 Internal Server Error response
        logger.error(f'Error: {e}')
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        # Close the session
        session.close()



from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, DataError
from yourapp import app, db
from yourapp.models import AttendanceRecord, Teacher
from yourapp.utils import validate_input, validate_status

@app.route('/teacher/attendance/<int:attendance_id>', methods=['PUT'])
@jwt_required()
def update_teacher_attendance(attendance_id):
    """
    Update teacher attendance record.

    :param attendance_id: The ID of the attendance record to update.
    :return: A JSON response with a message indicating the result of the update operation.
    """
    try:
        # Get the current user's identity from the JWT token
        current_user = get_jwt_identity()

        # Validate the request body
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No request body provided'}), 400

        # Validate the status field in the request body
        if 'status' not in data:
            return jsonify({'message': 'Status field is required'}), 400
        status = data['status']
        if not validate_status(status):
            return jsonify({'message': 'Invalid status'}), 400

        # Check if the attendance record exists
        attendance_record = AttendanceRecord.query.get(attendance_id)
        if not attendance_record:
            return jsonify({'message': 'Attendance record not found'}), 404

        # Check if the current user is a teacher and has permission to update the attendance record
        teacher = Teacher.query.filter_by(username=current_user).first()
        if not teacher:
            return jsonify({'message': 'Forbidden'}), 403
        if attendance_record.teacher_id != teacher.id:
            return jsonify({'message': 'Forbidden'}), 403

        # Update the attendance record
        attendance_record.status = status
        db.session.commit()

        return jsonify({'message': 'Attendance record updated successfully'}), 200

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'message': 'Database integrity error'}), 500
    except DataError as e:
        db.session.rollback()
        return jsonify({'message': 'Invalid data'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred'}), 500
