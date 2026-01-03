# Flask Backend API

This Flask backend was automatically generated based on your application design.

## Endpoints Created

1. **POST /api/auth/login** - login
2. **POST /api/auth/forgot-password** - forgot_password
3. **POST /api/auth/register** - register
4. **GET /api/auth/validate-username** - validate_username
5. **POST /api/auth/validate-password** - validate_password
6. **GET /api/auth/user-role** - get_user_role
7. **POST /api/auth/login-attempt** - login_attempt
8. **POST /api/register** - Register User
9. **GET /api/validate-email** - Validate Email
10. **GET /api/validate-username** - Validate Username
11. **GET /api/roles** - Get Roles
12. **GET /api/terms-and-conditions** - Get Terms and Conditions
13. **POST /api/check-password-strength** - Check Password Strength
14. **GET /api/user/details** - Get User Details
15. **POST /api/attendance/mark** - Mark Attendance
16. **GET /api/attendance/records** - Get Attendance Records
17. **GET /api/attendance/history** - Get Attendance History
18. **GET /api/attendance/patterns** - Get Attendance Patterns
19. **GET /api/menu/items** - Get Navigation Menu
20. **GET /api/calendar/data** - Get Calendar
21. **GET /api/attendance/records/filter** - Filter Attendance Records
22. **GET /api/notifications** - Get Notifications
23. **GET /api/attendance/statistics** - Get Attendance Statistics
24. **GET /api/attendance/records/search** - Search Attendance Records
25. **GET /api/profile** - Get User Profile
26. **PUT /api/profile** - Update User Profile
27. **POST /api/profile/picture** - Upload Profile Picture
28. **POST /api/profile/password** - Change Password
29. **POST /api/profile/validate** - Validate Profile Updates
30. **POST /api/password-recovery/send-email** - Send Password Recovery Email
31. **POST /api/password-recovery/validate-credentials** - Validate Username or Email
32. **POST /api/password-recovery/resend-email** - Resend Password Recovery Email
33. **PUT /api/password-recovery/reset-password** - Reset Password
34. **GET /api/password-recovery/verify-token** - Verify Password Recovery Token
35. **GET /api/student/details** - Get Student Details
36. **GET /api/attendance/calendar** - Get Attendance Calendar
37. **POST /api/attendance/comment** - Add Attendance Comment
38. **GET /api/attendance/status** - Check Attendance Status
39. **GET /api/attendance/timeframe** - Validate Attendance Time Frame
40. **POST /api/authenticate/student** - Authenticate Student
41. **GET /api/students** - Get All Students
42. **GET /api/students/{studentId}/attendance** - Get Student Attendance Records
43. **GET /api/students/{studentId}/attendance?startDate={startDate}&endDate={endDate}** - Filter Attendance Records By Date Range
44. **GET /api/students/search?q={query}** - Search Students
45. **GET /api/students/{studentId}/attendance/history** - Get Detailed Attendance History
46. **GET /api/students/attendance/export/csv** - Export Attendance Records To CSV
47. **GET /api/students/attendance/export/excel** - Export Attendance Records To Excel
48. **GET /api/students?page={page}&size={size}** - Get Paginated Students List
49. **GET /api/students/{studentId}/profile** - Get Student Profile
50. **GET /api/students/{studentId}/attendance/history/byDateRange** - Get Attendance History By Date Range
51. **GET /api/students/{studentId}/attendance/history/search** - Search Attendance Records
52. **GET /api/students/{studentId}/attendance/history/export** - Export Attendance History
53. **GET /api/students/{studentId}/attendance/summary** - Get Attendance Summary
54. **GET /api/app-info** - Get Application Info
55. **GET /api/navigation-menu** - Get Navigation Menu
56. **GET /api/settings/search** - Search Settings
57. **GET /api/user-profile** - Get User Profile
58. **PUT /api/user-profile** - Update User Profile
59. **PUT /api/user-profile/password** - Change Password
60. **GET /api/account-settings** - Get Account Settings
61. **PUT /api/account-settings** - Update Account Settings
62. **GET /api/notification-preferences** - Get Notification Preferences
63. **PUT /api/notification-preferences** - Update Notification Preferences
64. **GET /api/user-roles** - Get User Roles and Permissions
65. **PUT /api/user-roles** - Update User Roles and Permissions
66. **GET /api/attendance-settings** - Get Attendance Settings
67. **PUT /api/attendance-settings** - Update Attendance Settings
68. **GET /api/system-defaults** - Get System Defaults
69. **PUT /api/system-defaults** - Update System Defaults
70. **POST /api/settings/reset** - Reset Settings to Default
71. **POST /api/settings/save** - Save Settings Changes
72. **POST /api/settings/validate** - Validate Settings Changes
73. **POST /api/forgot-password** - Initiate Password Recovery
74. **POST /api/validate-credentials** - Validate User Credentials
75. **POST /api/send-recovery-email** - Send Recovery Email
76. **GET /api/check-username-email** - Check Username or Email Availability
77. **POST /api/user-roles** - Create New User Role
78. **GET /api/user-roles/{roleId}** - Get User Role By ID
79. **PUT /api/user-roles/{roleId}** - Update User Role
80. **DELETE /api/user-roles/{roleId}** - Delete User Role
81. **GET /api/users** - Get All Users With Roles
82. **POST /api/users/{userId}/roles** - Assign Role To User
83. **DELETE /api/users/{userId}/roles/{roleId}** - Unassign Role From User
84. **GET /api/search** - Search Users Or Roles
85. **GET /api/users/paginated** - Get Paginated Users
86. **GET /api/user-roles/paginated** - Get Paginated User Roles
87. **GET /api/stats** - Get User Count And Role Count
88. **GET /api/users/by-role/{roleId}** - Get Users By Role
89. **GET /api/users/sorted** - Get Sorted Users
90. **GET /api/homepage** - Get Homepage Link
91. **GET /api/dashboard** - Get Dashboard Link
92. **GET /api/previous-page** - Get Previous Page
93. **GET /api/contact** - Get Contact Link
94. **POST /api/report-issue** - Report Issue
95. **POST /api/errors** - Log Error
96. **GET /api/errors/{errorId}** - Get Error Details
97. **POST /api/errors/{errorId}/report** - Report Issue
98. **GET /api/attendance/records/:studentId** - Get Student Attendance Records
99. **GET /api/attendance/class-statistics** - Get Class Attendance Statistics
100. **GET /api/students/search** - Search Students
101. **GET /api/attendance/data** - Get Attendance Data
102. **GET /api/attendance/visualization-data** - Get Attendance Visualization Data
103. **GET /api/attendance/percentage/:studentId** - Get Student Attendance Percentage
104. **GET /api/students/filter** - Filter Students
105. **GET /api/students/dashboard** - Get Student Dashboard
106. **GET /api/students/{studentId}/profile-picture** - Get Student Profile Picture
107. **GET /api/students/{studentId}/contact-info** - Get Student Contact Information
108. **GET /api/students/{studentId}/attendance/details** - Get Detailed Attendance Records
109. **POST /api/auth/teacher/login** - Authenticate Teacher

## Getting Started

1. Navigate to the backend directory:
   ```bash
   cd project\backend
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
project\backend/
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
