import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Import all page components
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import StudentDashboard from './pages/StudentDashboard';
import StudentAttendanceMarkingPage from './pages/StudentAttendanceMarkingPage';
import TeacherDashboard from './pages/TeacherDashboard';
import TeacherAttendanceRecordManagementPage from './pages/TeacherAttendanceRecordManagementPage';
import ProfileManagementPage from './pages/ProfileManagementPage';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h2>Application Navigation</h2>
          <ul>
            <li><Link to="/login-page">Login Page</Link></li>
            <li><Link to="/registration-page">Registration Page</Link></li>
            <li><Link to="/student-dashboard">Student Dashboard</Link></li>
            <li><Link to="/student-attendance-marking-page">Student Attendance Marking Page</Link></li>
            <li><Link to="/teacher-dashboard">Teacher Dashboard</Link></li>
            <li><Link to="/teacher-attendance-record-management-page">Teacher Attendance Record Management Page</Link></li>
            <li><Link to="/profile-management-page">Profile Management Page</Link></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/login-page" element={<LoginPage />} />
            <Route path="/registration-page" element={<RegistrationPage />} />
            <Route path="/student-dashboard" element={<StudentDashboard />} />
            <Route path="/student-attendance-marking-page" element={<StudentAttendanceMarkingPage />} />
            <Route path="/teacher-dashboard" element={<TeacherDashboard />} />
            <Route path="/teacher-attendance-record-management-page" element={<TeacherAttendanceRecordManagementPage />} />
            <Route path="/profile-management-page" element={<ProfileManagementPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
