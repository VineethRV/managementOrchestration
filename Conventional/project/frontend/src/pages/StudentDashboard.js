import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

/**
 * Student Dashboard component.
 * 
 * Displays attendance summary and history for the student.
 * 
 * @returns {JSX.Element} The Student Dashboard component.
 */
const StudentDashboard = () => {
  // State to store attendance summary and history
  const [attendanceSummary, setAttendanceSummary] = useState({
    totalDays: 0,
    presentDays: 0,
    absentDays: 0,
  });
  const [attendanceHistory, setAttendanceHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Axios instance with base URL
  const api = axios.create({
    baseURL: 'http://localhost:5000',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
  });

  // Navigate function from react-router-dom
  const navigate = useNavigate();

  // Callback function to fetch attendance summary
  const fetchAttendanceSummary = useCallback(async () => {
    try {
      const response = await api.get('/student/attendance/summary');
      setAttendanceSummary(response.data.attendance_summary);
    } catch (error) {
      setError(error.message);
    }
  }, [api]);

  // Callback function to fetch attendance history
  const fetchAttendanceHistory = useCallback(async () => {
    try {
      const response = await api.get('/student/attendance/history');
      setAttendanceHistory(response.data.attendance_history);
    } catch (error) {
      setError(error.message);
    }
  }, [api]);

  // Effect to fetch attendance summary and history on mount
  useEffect(() => {
    const fetchAttendanceData = async () => {
      await fetchAttendanceSummary();
      await fetchAttendanceHistory();
      setLoading(false);
    };
    fetchAttendanceData();
  }, [fetchAttendanceSummary, fetchAttendanceHistory]);

  // Render loading state
  if (loading) {
    return (
      <div className="loading-state">
        <h2>Loading...</h2>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="error-state">
        <h2>Error: {error}</h2>
      </div>
    );
  }

  // Render attendance summary and history
  return (
    <div className="student-dashboard">
      <h1>Student Dashboard</h1>
      <section className="attendance-summary">
        <h2>Attendance Summary</h2>
        <ul>
          <li>Total Days: {attendanceSummary.totalDays}</li>
          <li>Present Days: {attendanceSummary.presentDays}</li>
          <li>Absent Days: {attendanceSummary.absentDays}</li>
        </ul>
      </section>
      <section className="attendance-history">
        <h2>Attendance History</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {attendanceHistory.map((attendance, index) => (
              <tr key={index}>
                <td>{attendance.date}</td>
                <td>{attendance.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default StudentDashboard;
