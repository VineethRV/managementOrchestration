
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# Define models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)

class StudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True

class AttendanceRecordSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AttendanceRecord
        load_instance = True

# Define schemas
student_schema = StudentSchema()
students_schema = StudentSchema(many=True)
attendance_record_schema = AttendanceRecordSchema()
attendance_records_schema = AttendanceRecordSchema(many=True)

# Define helper functions
def get_student(student_id):
    try:
        return Student.query.get(student_id)
    except Exception as e:
        logging.error(f"Error getting student: {e}")
        return None

def get_attendance_records(student_id):
    try:
        return AttendanceRecord.query.filter_by(student_id=student_id).all()
    except Exception as e:
        logging.error(f"Error getting attendance records: {e}")
        return None

# Define routes
@app.route('/api/students', methods=['GET'])
def get_all_students():
    """
    Retrieve a list of all students
    """
    try:
        students = Student.query.all()
        return jsonify(students_schema.dump(students)), 200
    except Exception as e:
        logging.error(f"Error getting all students: {e}")
        return jsonify({"message": "Error getting all students"}), 500

@app.route('/api/students/<int:student_id>/attendance', methods=['GET'])
def get_student_attendance_records(student_id):
    """
    Retrieve attendance records for a specific student
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = get_attendance_records(student_id)
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error getting attendance records: {e}")
        return jsonify({"message": "Error getting attendance records"}), 500

@app.route('/api/students/<int:student_id>/attendance', methods=['GET'])
def filter_attendance_records_by_date_range(student_id):
    """
    Retrieve attendance records for a specific date range
    """
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        if start_date is None or end_date is None:
            return jsonify({"message": "Start date and end date are required"}), 400
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = AttendanceRecord.query.filter_by(student_id=student_id).filter(AttendanceRecord.date >= start_date).filter(AttendanceRecord.date <= end_date).all()
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error filtering attendance records: {e}")
        return jsonify({"message": "Error filtering attendance records"}), 500

@app.route('/api/students/search', methods=['GET'])
def search_students():
    """
    Search for specific students by name or ID
    """
    try:
        query = request.args.get('q')
        if query is None:
            return jsonify({"message": "Query is required"}), 400
        students = Student.query.filter((Student.name.like(f"%{query}%")) | (Student.id == query)).all()
        return jsonify(students_schema.dump(students)), 200
    except Exception as e:
        logging.error(f"Error searching students: {e}")
        return jsonify({"message": "Error searching students"}), 500

@app.route('/api/students/<int:student_id>/attendance/history', methods=['GET'])
def get_detailed_attendance_history(student_id):
    """
    Retrieve detailed attendance history for a specific student
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = get_attendance_records(student_id)
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error getting attendance history: {e}")
        return jsonify({"message": "Error getting attendance history"}), 500

@app.route('/api/students/attendance/export/csv', methods=['GET'])
def export_attendance_records_to_csv():
    """
    Export attendance records to CSV
    """
    try:
        attendance_records = AttendanceRecord.query.all()
        csv_data = []
        for record in attendance_records:
            csv_data.append({
                'student_id': record.student_id,
                'date': record.date,
                'status': record.status
            })
        return jsonify(csv_data), 200
    except Exception as e:
        logging.error(f"Error exporting attendance records to CSV: {e}")
        return jsonify({"message": "Error exporting attendance records to CSV"}), 500

@app.route('/api/students/attendance/export/excel', methods=['GET'])
def export_attendance_records_to_excel():
    """
    Export attendance records to Excel
    """
    try:
        attendance_records = AttendanceRecord.query.all()
        excel_data = []
        for record in attendance_records:
            excel_data.append({
                'student_id': record.student_id,
                'date': record.date,
                'status': record.status
            })
        return jsonify(excel_data), 200
    except Exception as e:
        logging.error(f"Error exporting attendance records to Excel: {e}")
        return jsonify({"message": "Error exporting attendance records to Excel"}), 500

@app.route('/api/students/<int:student_id>/profile', methods=['GET'])
def get_student_profile(student_id):
    """
    Retrieve student's profile information
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        return jsonify(student_schema.dump(student)), 200
    except Exception as e:
        logging.error(f"Error getting student profile: {e}")
        return jsonify({"message": "Error getting student profile"}), 500

@app.route('/api/students/<int:student_id>/attendance/history/byDateRange', methods=['GET'])
def get_attendance_history_by_date_range(student_id):
    """
    Retrieve student's attendance history for a specific date range
    """
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        if start_date is None or end_date is None:
            return jsonify({"message": "Start date and end date are required"}), 400
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = AttendanceRecord.query.filter_by(student_id=student_id).filter(AttendanceRecord.date >= start_date).filter(AttendanceRecord.date <= end_date).all()
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error getting attendance history by date range: {e}")
        return jsonify({"message": "Error getting attendance history by date range"}), 500

@app.route('/api/students/<int:student_id>/attendance/history/search', methods=['GET'])
def search_attendance_records(student_id):
    """
    Search for specific attendance records
    """
    try:
        query = request.args.get('q')
        if query is None:
            return jsonify({"message": "Query is required"}), 400
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = AttendanceRecord.query.filter_by(student_id=student_id).filter(AttendanceRecord.date.like(f"%{query}%")).all()
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error searching attendance records: {e}")
        return jsonify({"message": "Error searching attendance records"}), 500

@app.route('/api/students/<int:student_id>/attendance/history/export', methods=['GET'])
def export_attendance_history(student_id):
    """
    Export student's attendance history in CSV or PDF format
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = get_attendance_records(student_id)
        csv_data = []
        for record in attendance_records:
            csv_data.append({
                'date': record.date,
                'status': record.status
            })
        return jsonify(csv_data), 200
    except Exception as e:
        logging.error(f"Error exporting attendance history: {e}")
        return jsonify({"message": "Error exporting attendance history"}), 500

@app.route('/api/students/<int:student_id>/attendance/summary', methods=['GET'])
def get_attendance_summary(student_id):
    """
    Retrieve student's attendance summary (total days present, absent, percentage)
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = get_attendance_records(student_id)
        total_days_present = 0
        total_days_absent = 0
        for record in attendance_records:
            if record.status == 'present':
                total_days_present += 1
            elif record.status == 'absent':
                total_days_absent += 1
        attendance_percentage = (total_days_present / (total_days_present + total_days_absent)) * 100 if total_days_present + total_days_absent > 0 else 0
        return jsonify({
            'totalDaysPresent': total_days_present,
            'totalDaysAbsent': total_days_absent,
            'attendancePercentage': attendance_percentage
        }), 200
    except Exception as e:
        logging.error(f"Error getting attendance summary: {e}")
        return jsonify({"message": "Error getting attendance summary"}), 500

@app.route('/api/students/search', methods=['GET'])
def search_students_by_name():
    """
    Search for students by name
    """
    try:
        query = request.args.get('q')
        if query is None:
            return jsonify({"message": "Query is required"}), 400
        students = Student.query.filter(Student.name.like(f"%{query}%")).all()
        return jsonify(students_schema.dump(students)), 200
    except Exception as e:
        logging.error(f"Error searching students: {e}")
        return jsonify({"message": "Error searching students"}), 500

@app.route('/api/students/filter', methods=['GET'])
def filter_students():
    """
    Filter students by class or attendance status
    """
    try:
        class_id = request.args.get('classId')
        attendance_status = request.args.get('attendanceStatus')
        if class_id is None and attendance_status is None:
            return jsonify({"message": "Class ID or attendance status is required"}), 400
        students = Student.query.all()
        filtered_students = []
        for student in students:
            if class_id is not None and student.class_id == class_id:
                filtered_students.append(student)
            elif attendance_status is not None and student.attendance_status == attendance_status:
                filtered_students.append(student)
        return jsonify(students_schema.dump(filtered_students)), 200
    except Exception as e:
        logging.error(f"Error filtering students: {e}")
        return jsonify({"message": "Error filtering students"}), 500

@app.route('/api/students/dashboard', methods=['GET'])
@jwt_required
def get_student_dashboard():
    """
    Retrieve dashboard view for teachers to overview student attendance
    """
    try:
        students = Student.query.all()
        return jsonify(students_schema.dump(students)), 200
    except Exception as e:
        logging.error(f"Error getting student dashboard: {e}")
        return jsonify({"message": "Error getting student dashboard"}), 500

@app.route('/api/students/<int:student_id>/profile-picture', methods=['GET'])
def get_student_profile_picture(student_id):
    """
    Retrieve student profile picture
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        return jsonify({'profilePicture': student.profile_picture}), 200
    except Exception as e:
        logging.error(f"Error getting student profile picture: {e}")
        return jsonify({"message": "Error getting student profile picture"}), 500

@app.route('/api/students/<int:student_id>/contact-info', methods=['GET'])
def get_student_contact_information(student_id):
    """
    Retrieve student contact information
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        return jsonify({'phone': student.phone, 'email': student.email}), 200
    except Exception as e:
        logging.error(f"Error getting student contact information: {e}")
        return jsonify({"message": "Error getting student contact information"}), 500

@app.route('/api/students/<int:student_id>/attendance/details', methods=['GET'])
def get_detailed_attendance_records(student_id):
    """
    Retrieve detailed attendance records for a student
    """
    try:
        student = get_student(student_id)
        if student is None:
            return jsonify({"message": "Student not found"}), 404
        attendance_records = get_attendance_records(student_id)
        return jsonify(attendance_records_schema.dump(attendance_records)), 200
    except Exception as e:
        logging.error(f"Error getting attendance records: {e}")
        return jsonify({"message": "Error getting attendance records"}), 500

if __name__ == '__main__':
    app.run(debug=True)
