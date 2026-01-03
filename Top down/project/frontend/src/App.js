import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Import all page components
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import Dashboard from './pages/Dashboard';
import ProfileManagement from './pages/ProfileManagement';
import PasswordRecovery from './pages/PasswordRecovery';
import AttendanceMarking from './pages/AttendanceMarking';
import AttendanceRecords from './pages/AttendanceRecords';
import AttendanceHistory from './pages/AttendanceHistory';
import Settings from './pages/Settings';
import ForgotPassword from './pages/ForgotPassword';
import UserRolesManagement from './pages/UserRolesManagement';
import Error404Page from './pages/Error404Page';
import Error500Page from './pages/Error500Page';
import AttendanceAnalytics from './pages/AttendanceAnalytics';
import StudentInformation from './pages/StudentInformation';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h2>Application Navigation</h2>
          <ul>
            <li><Link to="/login-page">Login Page</Link></li>
            <li><Link to="/registration-page">Registration Page</Link></li>
            <li><Link to="/dashboard">Dashboard</Link></li>
            <li><Link to="/profile-management">Profile Management</Link></li>
            <li><Link to="/password-recovery">Password Recovery</Link></li>
            <li><Link to="/attendance-marking">Attendance Marking</Link></li>
            <li><Link to="/attendance-records">Attendance Records</Link></li>
            <li><Link to="/attendance-history">Attendance History</Link></li>
            <li><Link to="/settings">Settings</Link></li>
            <li><Link to="/forgot-password">Forgot Password</Link></li>
            <li><Link to="/user-roles-management">User Roles Management</Link></li>
            <li><Link to="/error-404-page">Error 404 Page</Link></li>
            <li><Link to="/error-500-page">Error 500 Page</Link></li>
            <li><Link to="/attendance-analytics">Attendance Analytics</Link></li>
            <li><Link to="/student-information">Student Information</Link></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/login-page" element={<LoginPage />} />
            <Route path="/registration-page" element={<RegistrationPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile-management" element={<ProfileManagement />} />
            <Route path="/password-recovery" element={<PasswordRecovery />} />
            <Route path="/attendance-marking" element={<AttendanceMarking />} />
            <Route path="/attendance-records" element={<AttendanceRecords />} />
            <Route path="/attendance-history" element={<AttendanceHistory />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/user-roles-management" element={<UserRolesManagement />} />
            <Route path="/error-404-page" element={<Error404Page />} />
            <Route path="/error-500-page" element={<Error500Page />} />
            <Route path="/attendance-analytics" element={<AttendanceAnalytics />} />
            <Route path="/student-information" element={<StudentInformation />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
