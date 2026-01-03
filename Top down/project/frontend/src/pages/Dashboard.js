import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} User
 * @property {string} role
 * @property {string} name
 */

/**
 * @typedef {Object} AttendanceRecord
 * @property {number} student_id
 * @property {string} date
 * @property {string} attendance_status
 */

/**
 * @typedef {Object} AttendanceStatistics
 * @property {number} total_students
 * @property {number} present_count
 * @property {number} absent_count
 * @property {number} percentage
 */

/**
 * @typedef {Object} Notification
 * @property {number} id
 * @property {string} title
 * @property {string} message
 * @property {string} timestamp
 * @property {boolean} read
 */

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [attendanceStatistics, setAttendanceStatistics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [date, setDate] = useState(new Date());
  const [attendanceStatus, setAttendanceStatus] = useState('');
  const [searchStudentId, setSearchStudentId] = useState('');
  const [filteredRecords, setFilteredRecords] = useState([]);

  const axiosInstance = useMemo(() => {
    const instance = axios.create({
      baseURL: 'http://localhost:5000',
    });
    return instance;
  }, []);

  const getUserDetails = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/user/details');
      setUser(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getAttendanceRecords = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance/records');
      setAttendanceRecords(response.data.attendance_records);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getAttendanceStatistics = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance/statistics');
      setAttendanceStatistics(response.data.attendance_statistics);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getNotifications = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/notifications');
      setNotifications(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const markAttendance = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.post('/api/attendance/mark', {
        student_id: user.student_id,
        date: date.toISOString().split('T')[0],
        attendance_status: attendanceStatus,
      });
      if (response.data.status) {
        getAttendanceRecords();
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, user, date, attendanceStatus, getAttendanceRecords]);

  const searchAttendanceRecords = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.get('/api/attendance/records/search', {
        params: { student_id: searchStudentId },
      });
      setFilteredRecords(response.data.attendance_records);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, searchStudentId]);

  const filterAttendanceRecords = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.get('/api/attendance/records/filter', {
        params: { date: date.toISOString().split('T')[0] },
      });
      setFilteredRecords(response.data.filtered_records);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, date]);

  useEffect(() => {
    const fetchUserData = async () => {
      await getUserDetails();
      await getAttendanceRecords();
      await getAttendanceStatistics();
      await getNotifications();
      setLoading(false);
    };
    fetchUserData();
  }, [getUserDetails, getAttendanceRecords, getAttendanceStatistics, getNotifications]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>
        Welcome, {user.name} ({user.role})
      </p>
      {user.role === 'student' && (
        <form onSubmit={markAttendance}>
          <label>
            Date:
            <input
              type="date"
              value={date.toISOString().split('T')[0]}
              onChange={(event) => setDate(new Date(event.target.value))}
            />
          </label>
          <br />
          <label>
            Attendance Status:
            <select
              value={attendanceStatus}
              onChange={(event) => setAttendanceStatus(event.target.value)}
            >
              <option value="">Select</option>
              <option value="present">Present</option>
              <option value="absent">Absent</option>
            </select>
          </label>
          <br />
          <button type="submit">Mark Attendance</button>
        </form>
      )}
      {user.role === 'teacher' && (
        <div>
          <h2>Attendance Records</h2>
          <table>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Date</th>
                <th>Attendance Status</th>
              </tr>
            </thead>
            <tbody>
              {attendanceRecords.map((record) => (
                <tr key={record.student_id}>
                  <td>{record.student_id}</td>
                  <td>{record.date}</td>
                  <td>{record.attendance_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <form onSubmit={searchAttendanceRecords}>
            <label>
              Search by Student ID:
              <input
                type="number"
                value={searchStudentId}
                onChange={(event) => setSearchStudentId(event.target.value)}
              />
            </label>
            <br />
            <button type="submit">Search</button>
          </form>
          <form onSubmit={filterAttendanceRecords}>
            <label>
              Filter by Date:
              <input
                type="date"
                value={date.toISOString().split('T')[0]}
                onChange={(event) => setDate(new Date(event.target.value))}
              />
            </label>
            <br />
            <button type="submit">Filter</button>
          </form>
          <h2>Filtered Records</h2>
          <table>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Date</th>
                <th>Attendance Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.map((record) => (
                <tr key={record.student_id}>
                  <td>{record.student_id}</td>
                  <td>{record.date}</td>
                  <td>{record.attendance_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h2>Attendance Statistics</h2>
          <p>
            Total Students: {attendanceStatistics.total_students}
            <br />
            Present: {attendanceStatistics.present_count}
            <br />
            Absent: {attendanceStatistics.absent_count}
            <br />
            Percentage: {attendanceStatistics.percentage}%
          </p>
          <h2>Notifications</h2>
          <ul>
            {notifications.map((notification) => (
              <li key={notification.id}>
                {notification.title}: {notification.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
