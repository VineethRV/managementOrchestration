from flask import Flask, request, jsonify


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import Unauthorized, InternalServerError

# Create a Flask Blueprint
app = Blueprint('attendance', __name__)

# Create a SQLAlchemy engine
engine = create_engine('sqlite:///attendance.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Base class for declarative class definitions
Base = declarative_base()

# Define the Student model
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    attendance_status = Column(Integer)  # 0 for absent, 1 for present

# Create all tables in the engine
Base.metadata.create_all(engine)

@app.route('/teacher/dashboard', methods=['GET'])
@jwt_required
def get_teacher_dashboard():
    """
    Retrieve teacher attendance overview.

    Returns:
        A JSON response with attendance overview.
    """
    try:
        # Get the current user's identity
        current_user = get_jwt_identity()

        # Validate the user's role
        if current_user['role'] != 'TEACHER':
            raise Unauthorized('Only teachers can access this endpoint')

        # Create a new session
        session = Session()

        # Query the database for student attendance
        total_students = session.query(Student).count()
        present_students = session.query(Student).filter_by(attendance_status=1).count()
        absent_students = total_students - present_students

        # Close the session
        session.close()

        # Return the attendance overview
        return jsonify({
            'attendance_overview': {
                'total_students': total_students,
                'present_students': present_students,
                'absent_students': absent_students
            }
        }), 200

    except Unauthorized as e:
        return jsonify({'error': str(e)}), 401

    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
