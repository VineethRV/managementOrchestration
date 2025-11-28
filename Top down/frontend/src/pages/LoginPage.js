import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} LoginResponse
 * @property {string} token
 * @property {number} user_id
 * @property {string} username
 * @property {string} email
 */

/**
 * @typedef {Object} ErrorResponse
 * @property {string} message
 */

/**
 * @param {Object} props
 * @returns {JSX.Element}
 */
function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const backendBaseUrl = 'http://localhost:5000';

  const handleUsernameChange = useCallback((event) => {
    setUsername(event.target.value);
  }, []);

  const handlePasswordChange = useCallback((event) => {
    setPassword(event.target.value);
  }, []);

  const handleRememberMeChange = useCallback((event) => {
    setRememberMe(event.target.checked);
  }, []);

  const handleLogin = useCallback(async (event) => {
    event.preventDefault();
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${backendBaseUrl}/api/auth/login`, {
        username,
        password,
      });
      const loginResponse = /** @type {LoginResponse} */ (response.data);
      // Handle successful login
      console.log(loginResponse);
      if (rememberMe) {
        await axios.post(`${backendBaseUrl}/api/auth/save-credentials`, {
          username,
          password,
        });
      }
    } catch (error) {
      const errorResponse = /** @type {ErrorResponse} */ (error.response.data);
      setError(errorResponse.message);
    } finally {
      setLoading(false);
    }
  }, [username, password, rememberMe, backendBaseUrl]);

  const handleForgotPassword = useCallback(async () => {
    // Implement forgot password logic
    try {
      const response = await axios.post(`${backendBaseUrl}/api/auth/forgot-password`, {
        email: username,
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  }, [username, backendBaseUrl]);

  const handleCreateAccount = useCallback(() => {
    // Implement create account logic
    window.location.href = '/create-account';
  }, []);

  const handleClearCredentials = useCallback(async () => {
    try {
      await axios.delete(`${backendBaseUrl}/api/auth/clear-credentials`);
      console.log('Credentials cleared');
    } catch (error) {
      console.error(error);
    }
  }, [backendBaseUrl]);

  return (
    <div className="login-page">
      <h1>Login</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleLogin}>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={handleUsernameChange}
            placeholder="Username"
            aria-label="Username"
          />
        </label>
        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={handlePasswordChange}
            placeholder="Password"
            aria-label="Password"
          />
        </label>
        <label>
          Remember me:
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={handleRememberMeChange}
            aria-label="Remember me"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Login'}
        </button>
      </form>
      <p>
        <a href="#" onClick={handleForgotPassword}>
          Forgot password?
        </a>
      </p>
      <p>
        <a href="#" onClick={handleCreateAccount}>
          Create account
        </a>
      </p>
      <button type="button" onClick={handleClearCredentials}>
        Clear credentials
      </button>
    </div>
  );
}

export default LoginPage;
