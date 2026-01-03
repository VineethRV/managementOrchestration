# React Frontend

This project was automatically generated based on your application design.

## Pages Created

1. **Login Page** - Page for users to login and obtain access tokens
2. **Registration Page** - Page for new users to register and obtain access tokens
3. **Student Dashboard** - Page for students to view daily and historical attendance
4. **Student Attendance Marking Page** - Page for students to mark attendance
5. **Teacher Dashboard** - Page for teachers to view attendance overview and filter by date or student
6. **Teacher Attendance Record Management Page** - Page for teachers to view and update attendance records
7. **Profile Management Page** - Page for users to view and update profile details

## Getting Started

1. Navigate to the project directory:
   ```bash
   cd project/frontend
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Backend Integration

The frontend is configured to communicate with the Flask backend at `http://localhost:5000`.
Make sure the backend is running before testing API integrations.

## Project Structure

```
project/frontend/
├── src/
│   ├── pages/          # All page components
│   ├── App.js          # Main app with routing
│   └── App.css         # Global styles
└── package.json
```

## Next Steps

- Implement the TODO comments in each page component
- Connect to backend API endpoints
- Add state management (Redux, Context API, etc.) if needed
- Implement authentication flows
- Add form validation
- Style components according to your design system
