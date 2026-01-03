import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} AttendanceData
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
 * @typedef {Object} Student
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

/**
 * @param {Object} props
 * @returns {JSX.Element}
 */
const AttendanceAnalytics = () => {
  const [attendanceData, setAttendanceData] = useState([]);
  const [attendanceStatistics, setAttendanceStatistics] = useState({});
  const [classStatistics, setClassStatistics] = useState({});
  const [studentAttendancePercentage, setStudentAttendancePercentage] = useState({});
  const [students, setStudents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchAttendanceData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/attendance/data', {
        params: {
          filter_by: filterBy,
          sort_by: sortBy,
        },
      });
      setAttendanceData(response.data.attendance_data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [filterBy, sortBy, axiosInstance]);

  const fetchAttendanceStatistics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/attendance/statistics');
      setAttendanceStatistics(response.data.attendance_statistics);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchClassStatistics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/attendance/class-statistics');
      setClassStatistics(response.data.class_statistics);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchStudentAttendancePercentage = useCallback(async (studentId) => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(`/api/attendance/percentage/${studentId}`);
      setStudentAttendancePercentage((prev) => ({ ...prev, [studentId]: response.data.attendance_percentage }));
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/students/search', {
        params: {
          name: searchTerm,
        },
      });
      setStudents(response.data.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, axiosInstance]);

  const handleSearch = useCallback((event) => {
    setSearchTerm(event.target.value);
  }, []);

  const handleFilterByChange = useCallback((event) => {
    setFilterBy(event.target.value);
  }, []);

  const handleSortByChange = useCallback((event) => {
    setSortBy(event.target.value);
  }, []);

  const handleDateRangeChange = useCallback((event) => {
    setDateRange((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  }, []);

  const handleStudentSelect = useCallback((studentId) => {
    setSelectedStudent(studentId);
  }, []);

  useEffect(() => {
    fetchAttendanceData();
    fetchAttendanceStatistics();
    fetchClassStatistics();
  }, [fetchAttendanceData, fetchAttendanceStatistics, fetchClassStatistics]);

  useEffect(() => {
    if (searchTerm) {
      fetchStudents();
    }
  }, [searchTerm, fetchStudents]);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentAttendancePercentage(selectedStudent);
    }
  }, [selectedStudent, fetchStudentAttendancePercentage]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Attendance Analytics</h1>
      <form>
        <label>
          Search for students:
          <input type="search" value={searchTerm} onChange={handleSearch} />
        </label>
        <label>
          Filter by:
          <select value={filterBy} onChange={handleFilterByChange}>
            <option value="">All</option>
            <option value="date">Date</option>
            <option value="student">Student</option>
            <option value="class">Class</option>
          </select>
        </label>
        <label>
          Sort by:
          <select value={sortBy} onChange={handleSortByChange}>
            <option value="">Default</option>
            <option value="date">Date</option>
            <option value="attendance_status">Attendance Status</option>
          </select>
        </label>
        <label>
          Date range:
          <input type="date" name="start" value={dateRange.start} onChange={handleDateRangeChange} />
          <input type="date" name="end" value={dateRange.end} onChange={handleDateRangeChange} />
        </label>
      </form>
      <h2>Attendance Statistics</h2>
      <p>Total students: {attendanceStatistics.total_students}</p>
      <p>Present count: {attendanceStatistics.present_count}</p>
      <p>Absent count: {attendanceStatistics.absent_count}</p>
      <p>Percentage: {attendanceStatistics.percentage}%</p>
      <h2>Class Statistics</h2>
      <p>Total students: {classStatistics.total_students}</p>
      <p>Present count: {classStatistics.present_count}</p>
      <p>Absent count: {classStatistics.absent_count}</p>
      <p>Percentage: {classStatistics.percentage}%</p>
      <h2>Student Attendance Percentage</h2>
      {students.map((student) => (
        <p key={student.id}>
          {student.name}: {studentAttendancePercentage[student.id]}%
          <button onClick={() => handleStudentSelect(student.id)}>View details</button>
        </p>
      ))}
      {selectedStudent && (
        <div>
          <h2>Attendance Records for {selectedStudent}</h2>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Attendance Status</th>
              </tr>
            </thead>
            <tbody>
              {attendanceData
                .filter((record) => record.student_id === selectedStudent)
                .map((record) => (
                  <tr key={record.date}>
                    <td>{record.date}</td>
                    <td>{record.attendance_status}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AttendanceAnalytics;
