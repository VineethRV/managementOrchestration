import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { toast } from 'react-toastify';

// Define schema for form validation
const filterSchema = yup.object().shape({
  date: yup.string().optional(),
  student: yup.string().optional(),
});

// Define the TeacherDashboard component
const TeacherDashboard = () => {
  // State to store attendance overview and records
  const [attendanceOverview, setAttendanceOverview] = useState({
    totalStudents: 0,
    presentStudents: 0,
    absentStudents: 0,
  });
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Use react-hook-form for form validation
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(filterSchema),
  });

  // Use axios to make API calls
  const api = axios.create({
    baseURL: 'http://localhost:5000',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
  });

  // Fetch attendance overview and records on component mount
  useEffect(() => {
    const fetchAttendanceOverview = async () => {
      try {
        setLoading(true);
        const response = await api.get('/teacher/dashboard');
        setAttendanceOverview(response.data.attendance_overview);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    const fetchAttendanceRecords = async () => {
      try {
        setLoading(true);
        const response = await api.get('/teacher/attendance');
        setAttendanceRecords(response.data.attendance_records);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAttendanceOverview();
    fetchAttendanceRecords();
  }, [api]);

  // Handle form submission to filter attendance records
  const handleFilter = useCallback(
    async (data) => {
      try {
        setLoading(true);
        const response = await api.get('/teacher/attendance', {
          params: {
            date: data.date,
            student: data.student,
          },
        });
        setAttendanceRecords(response.data.attendance_records);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    },
    [api]
  );

  // Render attendance overview and records
  return (
    <div className="teacher-dashboard">
      <h1>Teacher Dashboard</h1>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>Error: {error}</p>
      ) : (
        <div>
          <h2>Attendance Overview</h2>
          <ul>
            <li>Total Students: {attendanceOverview.totalStudents}</li>
            <li>Present Students: {attendanceOverview.presentStudents}</li>
            <li>Absent Students: {attendanceOverview.absentStudents}</li>
          </ul>
          <h2>Attendance Records</h2>
          <form onSubmit={handleSubmit(handleFilter)}>
            <label>
              Date:
              <input type="date" {...register('date')} />
              {errors.date && <p>{errors.date.message}</p>}
            </label>
            <label>
              Student:
              <input type="text" {...register('student')} />
              {errors.student && <p>{errors.student.message}</p>}
            </label>
            <button type="submit">Filter</button>
          </form>
          <table>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {attendanceRecords.map((record) => (
                <tr key={record.student_id}>
                  <td>{record.student_id}</td>
                  <td>{record.date}</td>
                  <td>{record.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TeacherDashboard;
