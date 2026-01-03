from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes (allows React frontend to communicate)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Configuration
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False

# Home route
@app.route('/')
def home():
    """API Home - List all available endpoints"""
    endpoints_list = []
    endpoints_list.append({"method": "POST", "path": "/auth/login", "description": "Login Endpoint"})
    endpoints_list.append({"method": "POST", "path": "/auth/register", "description": "Registration Endpoint"})
    endpoints_list.append({"method": "GET", "path": "/student/attendance/summary", "description": "Student Attendance Summary Endpoint"})
    endpoints_list.append({"method": "GET", "path": "/student/attendance/history", "description": "Student Attendance History Endpoint"})
    endpoints_list.append({"method": "POST", "path": "/student/attendance/mark", "description": "Student Attendance Marking Endpoint"})
    endpoints_list.append({"method": "GET", "path": "/teacher/dashboard", "description": "Teacher Dashboard Endpoint"})
    endpoints_list.append({"method": "GET", "path": "/teacher/attendance", "description": "Teacher Attendance Endpoint"})
    endpoints_list.append({"method": "PUT", "path": "/teacher/attendance/{attendanceId}", "description": "Teacher Attendance Record Management Endpoint"})
    endpoints_list.append({"method": "GET", "path": "/user/profile", "description": "User Profile Endpoint"})
    endpoints_list.append({"method": "PUT", "path": "/user/profile", "description": "User Profile Update Endpoint"})
    
    return jsonify({
        "message": "Flask Backend API",
        "total_endpoints": len(endpoints_list),
        "endpoints": endpoints_list
    })


@app.route('/auth/login', methods=['POST'])
def login_endpoint():
    """
    Login Endpoint
    Authenticate user and issue access token
    
    Request: {'username': 'string', 'password': 'string'}
    Response: {'token': 'string', 'role': 'string'}
    """
    # TODO: Implement Login Endpoint
    try:
        
        data = request.get_json()
        # TODO: Validate and save data to database
        response_data = {"message": "POST /auth/login - Not implemented yet", "received": data}
        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/auth/register', methods=['POST'])
def registration_endpoint():
    """
    Registration Endpoint
    Register new user and issue access token
    
    Request: {'username': 'string', 'password': 'string', 'role': 'string'}
    Response: {'token': 'string', 'role': 'string'}
    """
    # TODO: Implement Registration Endpoint
    try:
        
        data = request.get_json()
        # TODO: Validate and save data to database
        response_data = {"message": "POST /auth/register - Not implemented yet", "received": data}
        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/student/attendance/summary', methods=['GET'])
def student_attendance_summary_endpoint():
    """
    Student Attendance Summary Endpoint
    Retrieve student attendance summary
    
    Request: None
    Response: {'attendance_summary': {'total_days': 'integer', 'present_days': 'integer', 'absent_days': 'integer'}}
    """
    # TODO: Implement Student Attendance Summary Endpoint
    try:
        
        # TODO: Fetch data from database
        data = {"message": "GET /student/attendance/summary - Not implemented yet"}
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/student/attendance/history', methods=['GET'])
def student_attendance_history_endpoint():
    """
    Student Attendance History Endpoint
    Retrieve student attendance history
    
    Request: None
    Response: {'attendance_history': [{'date': 'string', 'status': 'string'}]}
    """
    # TODO: Implement Student Attendance History Endpoint
    try:
        
        # TODO: Fetch data from database
        data = {"message": "GET /student/attendance/history - Not implemented yet"}
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/student/attendance/mark', methods=['POST'])
def student_attendance_marking_endpoint():
    """
    Student Attendance Marking Endpoint
    Mark student attendance for the day
    
    Request: None
    Response: {'message': 'string'}
    """
    # TODO: Implement Student Attendance Marking Endpoint
    try:
        
        data = request.get_json()
        # TODO: Validate and save data to database
        response_data = {"message": "POST /student/attendance/mark - Not implemented yet", "received": data}
        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/teacher/dashboard', methods=['GET'])
def teacher_dashboard_endpoint():
    """
    Teacher Dashboard Endpoint
    Retrieve teacher attendance overview
    
    Request: None
    Response: {'attendance_overview': {'total_students': 'integer', 'present_students': 'integer', 'absent_students': 'integer'}}
    """
    # TODO: Implement Teacher Dashboard Endpoint
    try:
        
        # TODO: Fetch data from database
        data = {"message": "GET /teacher/dashboard - Not implemented yet"}
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/teacher/attendance', methods=['GET'])
def teacher_attendance_endpoint():
    """
    Teacher Attendance Endpoint
    Retrieve teacher attendance records
    
    Request: None
    Response: {'attendance_records': [{'student_id': 'integer', 'date': 'string', 'status': 'string'}]}
    """
    # TODO: Implement Teacher Attendance Endpoint
    try:
        
        # TODO: Fetch data from database
        data = {"message": "GET /teacher/attendance - Not implemented yet"}
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/teacher/attendance/<attendanceId>', methods=['PUT'])
def teacher_attendance_record_management_endpoint():
    """
    Teacher Attendance Record Management Endpoint
    Update teacher attendance record
    
    Request: {'status': 'string'}
    Response: {'message': 'string'}
    """
    # TODO: Implement Teacher Attendance Record Management Endpoint
    try:
        
        data = request.get_json()
        # TODO: Update data in database
        response_data = {"message": "PUT /teacher/attendance/{attendanceId} - Not implemented yet", "received": data}
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/user/profile', methods=['GET'])
def user_profile_endpoint():
    """
    User Profile Endpoint
    Retrieve user profile details
    
    Request: None
    Response: {'profile_details': {'username': 'string', 'role': 'string'}}
    """
    # TODO: Implement User Profile Endpoint
    try:
        
        # TODO: Fetch data from database
        data = {"message": "GET /user/profile - Not implemented yet"}
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/user/profile', methods=['PUT'])
def user_profile_update_endpoint():
    """
    User Profile Update Endpoint
    Update user profile details
    
    Request: {'username': 'string', 'role': 'string'}
    Response: {'message': 'string'}
    """
    # TODO: Implement User Profile Update Endpoint
    try:
        
        data = request.get_json()
        # TODO: Update data in database
        response_data = {"message": "PUT /user/profile - Not implemented yet", "received": data}
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
