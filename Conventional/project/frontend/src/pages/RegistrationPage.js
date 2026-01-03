import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Link, useNavigate } from 'react-router-dom';

// Define schema for form validation
const schema = yup.object().shape({
  username: yup.string().required('Username is required'),
  password: yup.string().required('Password is required').min(8, 'Password must be at least 8 characters'),
  role: yup.string().required('Role is required').oneOf(['STUDENT', 'TEACHER'], 'Invalid role'),
});

const RegistrationPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  // Initialize form with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
  });

  // Handle form submission
  const onSubmit = useCallback(
    async (data) => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.post('http://localhost:5000/auth/register', data);
        setSuccess(true);
        navigate('/login', { replace: true });
      } catch (error) {
        if (axios.isAxiosError(error)) {
          setError(error.response.data.message);
        } else {
          setError('An unknown error occurred');
        }
        setLoading(false);
      }
    },
    [navigate]
  );

  return (
    <main className="registration-page">
      <h1>Registration Page</h1>
      {success ? (
        <p>Registration successful! You will be redirected to the login page.</p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <label htmlFor="username">
            Username:
            <input
              type="text"
              id="username"
              {...register('username')}
              aria-invalid={errors.username ? 'true' : 'false'}
            />
            {errors.username && <p role="alert">{errors.username.message}</p>}
          </label>
          <label htmlFor="password">
            Password:
            <input
              type="password"
              id="password"
              {...register('password')}
              aria-invalid={errors.password ? 'true' : 'false'}
            />
            {errors.password && <p role="alert">{errors.password.message}</p>}
          </label>
          <label htmlFor="role">
            Role:
            <select id="role" {...register('role')} aria-invalid={errors.role ? 'true' : 'false'}>
              <option value="">Select a role</option>
              <option value="STUDENT">Student</option>
              <option value="TEACHER">Teacher</option>
            </select>
            {errors.role && <p role="alert">{errors.role.message}</p>}
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </button>
          {error && <p role="alert" style={{ color: 'red' }}>
            {error}
          </p>}
        </form>
      )}
      <p>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </main>
  );
};

export default RegistrationPage;
