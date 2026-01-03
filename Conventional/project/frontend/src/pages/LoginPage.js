import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

/**
 * Login Page Component
 * 
 * Handles user login and obtains access token
 */
const LoginPage = () => {
  // State to store username and password
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);

  // Navigate to protected routes after login
  const navigate = useNavigate();

  // Validate form inputs
  const validateForm = useCallback(() => {
    if (!username || !password) {
      setError('Please fill in all fields');
      return false;
    }
    if (username.length < 3 || username.length > 20) {
      setError('Username must be between 3 and 20 characters');
      return false;
    }
    if (password.length < 8 || password.length > 50) {
      setError('Password must be between 8 and 50 characters');
      return false;
    }
    return true;
  }, [username, password]);

  // Handle login form submission
  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    if (!validateForm()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:5000/auth/login', {
        username,
        password,
      });
      const { token, role } = response.data;
      setToken(token);
      setRole(role);
      // Store token and role in local storage
      localStorage.setItem('token', token);
      localStorage.setItem('role', role);
      // Navigate to protected routes
      navigate('/dashboard');
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message);
      } else {
        setError('An error occurred');
      }
    } finally {
      setLoading(false);
    }
  }, [username, password, validateForm, navigate]);

  // Clear error message on input change
  const handleInputChange = useCallback(() => {
    setError(null);
  }, []);

  return (
    <main>
      <h1>Login Page</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="username">Username:</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(event) => {
            setUsername(event.target.value);
            handleInputChange();
          }}
          aria-required="true"
          aria-invalid={error ? 'true' : 'false'}
        />
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
            handleInputChange();
          }}
          aria-required="true"
          aria-invalid={error ? 'true' : 'false'}
        />
        {error && <p role="alert" aria-live="assertive">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Login'}
        </button>
      </form>
    </main>
  );
};

export default LoginPage;
