import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * Teacher Attendance Record Management Page Component
 * 
 * This component allows teachers to view and update attendance records.
 * 
 * @returns {JSX.Element} The component
 */
const TeacherAttendanceRecordManagementPage = () => {
  // State to store attendance record
  const [attendanceRecord, setAttendanceRecord] = useState(null);
  // State to store error message
  const [error, setError] = useState(null);
  // State to store loading state
  const [isLoading, setIsLoading] = useState(false);
  // State to store updated attendance status
  const [updatedStatus, setUpdatedStatus] = useState('');

  // Get attendance ID from URL parameters
  const { attendanceId } = useParams();
  // Get navigate function from react-router-dom
  const navigate = useNavigate();

  /**
   * Fetch attendance record from API
   * 
   * @async
   */
  const fetchAttendanceRecord = useCallback(async () => {
    try {
      // Set loading state to true
      setIsLoading(true);
      // Make GET request to API to fetch attendance record
      const response = await axios.get(`http://localhost:5000/teacher/attendance/${attendanceId}`);
      // Set attendance record state
      setAttendanceRecord(response.data);
    } catch (error) {
      // Set error state
      setError(error.message);
    } finally {
      // Set loading state to false
      setIsLoading(false);
    }
  }, [attendanceId]);

  /**
   * Update attendance record
   * 
   * @async
   */
  const updateAttendanceRecord = useCallback(async () => {
    try {
      // Set loading state to true
      setIsLoading(true);
      // Make PUT request to API to update attendance record
      const response = await axios.put(`http://localhost:5000/teacher/attendance/${attendanceId}`, {
        status: updatedStatus,
      });
      // Set attendance record state
      setAttendanceRecord(response.data);
      // Reset updated status state
      setUpdatedStatus('');
    } catch (error) {
      // Set error state
      setError(error.message);
    } finally {
      // Set loading state to false
      setIsLoading(false);
    }
  }, [attendanceId, updatedStatus]);

  // Fetch attendance record when component mounts
  useEffect(() => {
    fetchAttendanceRecord();
  }, [fetchAttendanceRecord]);

  // Handle form submission
  const handleSubmit = (event) => {
    event.preventDefault();
    updateAttendanceRecord();
  };

  // Handle input change
  const handleInputChange = (event) => {
    setUpdatedStatus(event.target.value);
  };

  // Render component
  return (
    <div>
      <h1>Teacher Attendance Record Management Page</h1>
      {isLoading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>Error: {error}</p>
      ) : attendanceRecord ? (
        <div>
          <h2>Attendance Record</h2>
          <p>Status: {attendanceRecord.status}</p>
          <form onSubmit={handleSubmit}>
            <label>
              Update Status:
              <select value={updatedStatus} onChange={handleInputChange}>
                <option value="">Select Status</option>
                <option value="present">Present</option>
                <option value="absent">Absent</option>
              </select>
            </label>
            <button type="submit">Update</button>
          </form>
        </div>
      ) : (
        <p>No attendance record found</p>
      )}
    </div>
  );
};

export default TeacherAttendanceRecordManagementPage;
