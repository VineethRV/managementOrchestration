# Flask Backend API

This Flask backend was automatically generated based on your application design.

## Endpoints Created

1. **POST /auth/login** - Login Endpoint
2. **POST /auth/register** - Registration Endpoint
3. **GET /student/attendance/summary** - Student Attendance Summary Endpoint
4. **GET /student/attendance/history** - Student Attendance History Endpoint
5. **POST /student/attendance/mark** - Student Attendance Marking Endpoint
6. **GET /teacher/dashboard** - Teacher Dashboard Endpoint
7. **GET /teacher/attendance** - Teacher Attendance Endpoint
8. **PUT /teacher/attendance/{attendanceId}** - Teacher Attendance Record Management Endpoint
9. **GET /user/profile** - User Profile Endpoint
10. **PUT /user/profile** - User Profile Update Endpoint

## Getting Started

1. Navigate to the backend directory:
   ```bash
   cd project/backend
   ```

2. Activate virtual environment:
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **Mac/Linux:**
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask server:
   ```bash
   python app.py
   ```

5. API will be available at [http://localhost:5000](http://localhost:5000)

## API Documentation

Visit `http://localhost:5000/` to see a list of all available endpoints.

## Project Structure

```
project/backend/
├── venv/              # Virtual environment
├── app.py             # Main Flask application
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Next Steps

- Implement the TODO comments in each endpoint
- Add database integration (SQLAlchemy recommended)
- Add authentication/authorization (JWT, Flask-Login, etc.)
- Add input validation
- Add logging
- Write unit tests
- Set up database migrations
- Add API documentation (Swagger/OpenAPI)

## CORS Configuration

CORS is enabled for `http://localhost:3000` to allow the React frontend to communicate with this backend.
Update the CORS configuration in `app.py` if your frontend runs on a different port.

## Environment Variables

Configure your environment in the `.env` file:
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (if using a database)
