import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} AttendanceRecord
 * @property {string} date
 * @property {string} status
 */

/**
 * @typedef {Object} AttendanceSummary
 * @property {number} totalDaysPresent
 * @property {number} totalDaysAbsent
 * @property {number} attendancePercentage
 */

/**
 * @typedef {Object} StudentProfile
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

/**
 * @param {number} studentId
 * @returns {JSX.Element}
 */
function AttendanceHistory({ studentId }) {
  const [attendanceHistory, setAttendanceHistory] = useState([]);
  const [attendanceSummary, setAttendanceSummary] = useState({});
  const [studentProfile, setStudentProfile] = useState({});
  const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [exportFormat, setExportFormat] = useState('csv');

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchStudentProfile = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/profile`);
      setStudentProfile(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, axiosInstance]);

  const fetchAttendanceHistory = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance/history`);
      setAttendanceHistory(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, axiosInstance]);

  const fetchAttendanceHistoryByDateRange = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance/history/byDateRange`, {
        params: dateRange,
      });
      setAttendanceHistory(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, dateRange, axiosInstance]);

  const fetchAttendanceSummary = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance/summary`);
      setAttendanceSummary(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [studentId, axiosInstance]);

  const handleDateRangeChange = (event) => {
    const { name, value } = event.target;
    setDateRange((prevDateRange) => ({ ...prevDateRange, [name]: value }));
  };

  const handleSearchQueryChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleExportFormatChange = (event) => {
    setExportFormat(event.target.value);
  };

  const handleExportAttendanceHistory = async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance/history/export`, {
        params: { format: exportFormat },
      });
      const blob = new Blob([response.data], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance-history.${exportFormat}`;
      a.click();
    } catch (error) {
      setError(error.message);
    }
  };

  const handleSearchAttendanceRecords = async () => {
    try {
      const response = await axiosInstance.get(`/api/students/${studentId}/attendance/history/search`, {
        params: { query: searchQuery },
      });
      setAttendanceHistory(response.data);
    } catch (error) {
      setError(error.message);
    }
  };

  useEffect(() => {
    fetchStudentProfile();
    fetchAttendanceHistory();
    fetchAttendanceSummary();
  }, [fetchStudentProfile, fetchAttendanceHistory, fetchAttendanceSummary]);

  const attendanceHistoryTable = useMemo(() => {
    return attendanceHistory.map((record) => (
      <tr key={record.date}>
        <td>{record.date}</td>
        <td>{record.status}</td>
      </tr>
    ));
  }, [attendanceHistory]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Attendance History</h1>
      <p>Student Name: {studentProfile.name}</p>
      <p>Student ID: {studentProfile.id}</p>
      <form>
        <label>
          Start Date:
          <input type="date" name="startDate" value={dateRange.startDate} onChange={handleDateRangeChange} />
        </label>
        <label>
          End Date:
          <input type="date" name="endDate" value={dateRange.endDate} onChange={handleDateRangeChange} />
        </label>
        <button type="button" onClick={fetchAttendanceHistoryByDateRange}>
          Filter by Date Range
        </button>
      </form>
      <form>
        <label>
          Search Query:
          <input type="search" value={searchQuery} onChange={handleSearchQueryChange} />
        </label>
        <button type="button" onClick={handleSearchAttendanceRecords}>
          Search Attendance Records
        </button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{attendanceHistoryTable}</tbody>
      </table>
      <p>Total Days Present: {attendanceSummary.totalDaysPresent}</p>
      <p>Total Days Absent: {attendanceSummary.totalDaysAbsent}</p>
      <p>Attendance Percentage: {attendanceSummary.attendancePercentage}%</p>
      <form>
        <label>
          Export Format:
          <select value={exportFormat} onChange={handleExportFormatChange}>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </select>
        </label>
        <button type="button" onClick={handleExportAttendanceHistory}>
          Export Attendance History
        </button>
      </form>
    </div>
  );
}

export default AttendanceHistory;
