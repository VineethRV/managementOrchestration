import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

/**
 * Student Attendance Marking Page component.
 * 
 * This component allows students to mark their attendance for the day.
 * 
 * @returns {JSX.Element} The Student Attendance Marking Page component.
 */
const StudentAttendanceMarkingPage = () => {
  // State to store the loading status of the component
  const [isLoading, setIsLoading] = useState(false);
  
  // State to store any error messages
  const [error, setError] = useState(null);
  
  // State to store the attendance marking status
  const [isAttendanceMarked, setIsAttendanceMarked] = useState(false);
  
  // State to store the JWT token for authentication
  const [token, setToken] = useState(() => {
    const storedToken = localStorage.getItem('token');
    return storedToken ? JSON.parse(storedToken) : null;
  });
  
  // Use the useNavigate hook to navigate to other pages
  const navigate = useNavigate();
  
  // Callback function to handle attendance marking
  const handleMarkAttendance = useCallback(async () => {
    // Check if the user is authenticated
    if (!token) {
      setError('You must be logged in to mark attendance');
      return;
    }
    
    // Set the loading state to true
    setIsLoading(true);
    
    try {
      // Make a POST request to the attendance marking endpoint
      const response = await axios.post('http://localhost:5000/student/attendance/mark', null, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // Check if the response was successful
      if (response.status === 200) {
        // Set the attendance marking status to true
        setIsAttendanceMarked(true);
        
        // Set the error state to null
        setError(null);
      } else {
        // Set the error state to the response message
        setError(response.data.message);
      }
    } catch (error) {
      // Set the error state to the error message
      setError(error.message);
    } finally {
      // Set the loading state to false
      setIsLoading(false);
    }
  }, [token]);
  
  // Use the useEffect hook to check if the user is authenticated on mount
  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);
  
  // Render the component
  return (
    <main>
      <h1>Mark Attendance</h1>
      
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <button onClick={handleMarkAttendance}>
          Mark Attendance
        </button>
      )}
      
      {error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : isAttendanceMarked ? (
        <p>Attendance marked successfully!</p>
      ) : null}
    </main>
  );
};

export default StudentAttendanceMarkingPage;
