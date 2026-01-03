import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} Student
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {string} class
 * @property {string} enrollmentNumber
 * @property {string} profilePicture
 * @property {Object} contactInfo
 * @property {string} contactInfo.phone
 * @property {string} contactInfo.email
 * @property {Object[]} attendanceRecords
 * @property {string} attendanceRecords.date
 * @property {string} attendanceRecords.status
 */

/**
 * @typedef {Object} Teacher
 * @property {number} id
 * @property {string} password
 */

/**
 * StudentInformation Component
 * @param {Object} props
 * @param {number} props.studentId
 * @returns {JSX.Element}
 */
function StudentInformation({ studentId }) {
  const [student, setStudent] = useState(null);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [teacherId, setTeacherId] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');

  const axiosInstance = useMemo(() => {
    const instance = axios.create({
      baseURL: 'http://localhost:5000',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return instance;
  }, [token]);

  const authenticateTeacher = useCallback(async () => {
    try {
      const response = await axios.post('/api/auth/teacher/login', {
        teacher_id: teacherId,
        password,
      });
      setToken(response.data.token);
      setAuthenticated(response.data.authorized);
    } catch (error) {
      setError(error.message);
    }
  }, [teacherId, password]);

  const getStudentProfile = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/profile`);
      setStudent(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, axiosInstance]);

  const getStudentAttendanceRecords = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance`);
      setAttendanceRecords(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, axiosInstance]);

  const searchStudents = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/students/search', {
        params: { query: searchQuery },
      });
      setFilteredStudents(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [searchQuery, axiosInstance]);

  const filterStudents = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/students/filter', {
        params: { class: student.class },
      });
      setFilteredStudents(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [student, axiosInstance]);

  useEffect(() => {
    if (authenticated) {
      getStudentProfile();
      getStudentAttendanceRecords();
    }
  }, [authenticated, getStudentProfile, getStudentAttendanceRecords]);

  const handleSearch = (event) => {
    event.preventDefault();
    searchStudents();
  };

  const handleFilter = (event) => {
    event.preventDefault();
    filterStudents();
  };

  const handleLogin = (event) => {
    event.preventDefault();
    authenticateTeacher();
  };

  if (!authenticated) {
    return (
      <div>
        <h1>Login as Teacher</h1>
        <form onSubmit={handleLogin}>
          <label>
            Teacher ID:
            <input type="number" value={teacherId} onChange={(event) => setTeacherId(event.target.value)} />
          </label>
          <br />
          <label>
            Password:
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <br />
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Student Information</h1>
      {student && (
        <div>
          <h2>{student.name}</h2>
          <p>Class: {student.class}</p>
          <p>Enrollment Number: {student.enrollmentNumber}</p>
          <img src={`/api/students/${studentId}/profile-picture`} alt={student.name} />
          <p>Contact Info:</p>
          <ul>
            <li>Phone: {student.contactInfo.phone}</li>
            <li>Email: {student.contactInfo.email}</li>
          </ul>
        </div>
      )}
      <h2>Attendance Records</h2>
      <ul>
        {attendanceRecords.map((record) => (
          <li key={record.date}>
            {record.date}: {record.status}
          </li>
        ))}
      </ul>
      <form onSubmit={handleSearch}>
        <label>
          Search Students:
          <input type="search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
        </label>
        <button type="submit">Search</button>
      </form>
      <ul>
        {filteredStudents.map((student) => (
          <li key={student.id}>
            {student.name}
          </li>
        ))}
      </ul>
      <form onSubmit={handleFilter}>
        <label>
          Filter by Class:
          <input type="text" value={student.class} onChange={(event) => setStudent({ ...student, class: event.target.value })} />
        </label>
        <button type="submit">Filter</button>
      </form>
    </div>
  );
}

export default StudentInformation;
