import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} StudentDetails
 * @property {number} student_id
 * @property {string} name
 * @property {string} email
 * @property {string} role
 */

/**
 * @typedef {Object} AttendanceCalendar
 * @property {Date} date
 * @property {boolean} is_holiday
 */

/**
 * @typedef {Object} AttendanceStatus
 * @property {boolean} attendance_status
 */

/**
 * @typedef {Object} AttendanceComment
 * @property {number} student_id
 * @property {Date} date
 * @property {string} comment
 */

/**
 * @typedef {Object} AttendanceTimeFrame
 * @property {boolean} is_within_timeframe
 */

/**
 * @param {Object} props
 * @returns {JSX.Element}
 */
const AttendanceMarking = () => {
  const [studentDetails, setStudentDetails] = useState(null);
  const [attendanceCalendar, setAttendanceCalendar] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [attendanceStatus, setAttendanceStatus] = useState(null);
  const [comment, setComment] = useState('');
  const [isWithinTimeframe, setIsWithinTimeframe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const getStudentDetails = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/student/details', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setStudentDetails(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getAttendanceCalendar = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance/calendar');
      setAttendanceCalendar(response.data.calendar_data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const markAttendance = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/attendance/mark', {
        student_id: studentDetails.student_id,
        date: selectedDate.toISOString().split('T')[0],
        attendance_status: attendanceStatus,
      });
      if (response.data.status) {
        alert('Attendance marked successfully!');
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, studentDetails, selectedDate, attendanceStatus]);

  const addAttendanceComment = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/attendance/comment', {
        student_id: studentDetails.student_id,
        date: selectedDate.toISOString().split('T')[0],
        comment: comment,
      });
      if (response.data.status) {
        alert('Comment added successfully!');
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, studentDetails, selectedDate, comment]);

  const checkAttendanceStatus = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance/status', {
        params: {
          date: selectedDate.toISOString().split('T')[0],
        },
      });
      setAttendanceStatus(response.data.attendance_status);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, selectedDate]);

  const validateAttendanceTimeFrame = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance/timeframe');
      setIsWithinTimeframe(response.data.is_within_timeframe);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const authenticateStudent = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/authenticate/student', {
        username: localStorage.getItem('username'),
        password: localStorage.getItem('password'),
      });
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        setIsAuthenticated(true);
      } else {
        setError(response.data.error);
      }
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    authenticateStudent();
  }, [authenticateStudent]);

  useEffect(() => {
    if (isAuthenticated) {
      getStudentDetails();
      getAttendanceCalendar();
      validateAttendanceTimeFrame();
    }
  }, [isAuthenticated, getStudentDetails, getAttendanceCalendar, validateAttendanceTimeFrame]);

  const handleDateChange = (date) => {
    setSelectedDate(date);
    checkAttendanceStatus();
  };

  const handleAttendanceStatusChange = (status) => {
    setAttendanceStatus(status);
  };

  const handleCommentChange = (event) => {
    setComment(event.target.value);
  };

  const handleMarkAttendance = () => {
    if (isWithinTimeframe) {
      markAttendance();
    } else {
      alert('Attendance marking is not allowed at this time.');
    }
  };

  const handleAddComment = () => {
    addAttendanceComment();
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!isAuthenticated) {
    return <div>Please authenticate to mark attendance.</div>;
  }

  return (
    <div>
      <h1>Attendance Marking</h1>
      <p>
        Student Name: {studentDetails ? studentDetails.name : 'Loading...'}
      </p>
      <input
        type="date"
        value={selectedDate.toISOString().split('T')[0]}
        onChange={(event) => handleDateChange(new Date(event.target.value))}
      />
      <select value={attendanceStatus} onChange={(event) => handleAttendanceStatusChange(event.target.value)}>
        <option value="">Select Attendance Status</option>
        <option value="present">Present</option>
        <option value="absent">Absent</option>
      </select>
      <textarea value={comment} onChange={handleCommentChange} />
      <button onClick={handleMarkAttendance}>Mark Attendance</button>
      <button onClick={handleAddComment}>Add Comment</button>
      {attendanceStatus === 'absent' && (
        <div>
          <label>Comment:</label>
          <textarea value={comment} onChange={handleCommentChange} />
        </div>
      )}
    </div>
  );
};

export default AttendanceMarking;
