import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} Student
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

/**
 * @typedef {Object} AttendanceRecord
 * @property {string} date
 * @property {string} status
 */

/**
 * AttendanceRecords component
 * @returns {JSX.Element}
 */
const AttendanceRecords = () => {
  const [students, setStudents] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({});
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalElements, setTotalElements] = useState(0);

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/students', {
        params: {
          page: pageNumber,
          size: pageSize,
        },
      });
      setStudents(response.data.content);
      setTotalPages(response.data.totalPages);
      setTotalElements(response.data.totalElements);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [pageNumber, pageSize, axiosInstance]);

  const fetchAttendanceRecords = useCallback(
    async (studentId) => {
      try {
        const response = await axiosInstance.get(
          `/api/students/${studentId}/attendance`,
          {
            params: {
              startDate: dateRange.startDate,
              endDate: dateRange.endDate,
            },
          }
        );
        setAttendanceRecords((prevRecords) => ({
          ...prevRecords,
          [studentId]: response.data,
        }));
      } catch (error) {
        setError(error.message);
      }
    },
    [dateRange, axiosInstance]
  );

  const handleSearch = useCallback(async (query) => {
    try {
      const response = await axiosInstance.get('/api/students/search', {
        params: {
          q: query,
        },
      });
      setFilteredStudents(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleDateRangeChange = useCallback((startDate, endDate) => {
    setDateRange({ startDate, endDate });
  }, []);

  const handlePageChange = useCallback((pageNumber) => {
    setPageNumber(pageNumber);
  }, []);

  const handlePageSizeChange = useCallback((pageSize) => {
    setPageSize(pageSize);
  }, []);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    if (students.length > 0) {
      students.forEach((student) => {
        fetchAttendanceRecords(student.id);
      });
    }
  }, [students, fetchAttendanceRecords]);

  const sortedStudents = useMemo(() => {
    if (searchQuery) {
      return filteredStudents;
    }
    return students;
  }, [searchQuery, filteredStudents, students]);

  const handleExportToCSV = async () => {
    try {
      const response = await axiosInstance.get('/api/students/attendance/export/csv', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'attendance-records.csv';
      a.click();
    } catch (error) {
      setError(error.message);
    }
  };

  const handleExportToExcel = async () => {
    try {
      const response = await axiosInstance.get('/api/students/attendance/export/excel', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'attendance-records.xlsx';
      a.click();
    } catch (error) {
      setError(error.message);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Attendance Records</h1>
      <input
        type="search"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search students"
        aria-label="Search students"
      />
      <button onClick={() => handleSearch(searchQuery)}>Search</button>
      <div>
        <label>
          Date Range:
          <input
            type="date"
            value={dateRange.startDate}
            onChange={(e) =>
              handleDateRangeChange(e.target.value, dateRange.endDate)
            }
            aria-label="Start date"
          />
          <input
            type="date"
            value={dateRange.endDate}
            onChange={(e) =>
              handleDateRangeChange(dateRange.startDate, e.target.value)
            }
            aria-label="End date"
          />
        </label>
      </div>
      <table>
        <thead>
          <tr>
            <th>Student Name</th>
            <th>Attendance Percentage</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedStudents.map((student) => (
            <tr key={student.id}>
              <td>{student.name}</td>
              <td>
                {attendanceRecords[student.id] && (
                  <span>
                    {attendanceRecords[student.id].filter((record) => record.status === 'present').length} /{' '}
                    {attendanceRecords[student.id].length}
                  </span>
                )}
              </td>
              <td>
                <button
                  onClick={() => fetchAttendanceRecords(student.id)}
                  aria-label={`View attendance records for ${student.name}`}
                >
                  View Attendance Records
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div>
        <button onClick={handleExportToCSV}>Export to CSV</button>
        <button onClick={handleExportToExcel}>Export to Excel</button>
      </div>
      <div>
        <label>
          Page Size:
          <select value={pageSize} onChange={(e) => handlePageSizeChange(e.target.value)}>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </label>
        <label>
          Page:
          <select value={pageNumber} onChange={(e) => handlePageChange(e.target.value)}>
            {Array.from({ length: totalPages }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {i + 1}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
};

export default AttendanceRecords;
