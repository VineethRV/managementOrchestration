import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} LoginProps
 * @property {function} onLoginSuccess
 */

/**
 * @param {LoginProps} props
 * @returns {JSX.Element}
 */
function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [isAccountLocked, setIsAccountLocked] = useState(false);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const handleUsernameChange = useCallback((event) => {
    setUsername(event.target.value);
  }, []);

  const handlePasswordChange = useCallback((event) => {
    setPassword(event.target.value);
  }, []);

  const handleRoleChange = useCallback((event) => {
    setRole(event.target.value);
  }, []);

  const handleRememberMeChange = useCallback((event) => {
    setRememberMe(event.target.checked);
  }, []);

  const handleLogin = useCallback(async (event) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await axiosInstance.post('/api/auth/login', {
        username,
        password,
      });

      if (response.data) {
        const { token, role, user_id } = response.data;
        onLoginSuccess(token, role, user_id);
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (error) {
      if (error.response) {
        if (error.response.status === 401) {
          setError('Invalid username or password');
        } else if (error.response.status === 429) {
          setIsAccountLocked(true);
          setError('Account locked due to excessive login attempts');
        } else {
          setError(error.response.data.message);
        }
      } else {
        setError(error.message);
      }
    } finally {
      setLoading(false);
    }
  }, [username, password, onLoginSuccess, axiosInstance]);

  const handleForgotPassword = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/auth/forgot-password', {
        email: username,
      });

      if (response.data) {
        alert('Password reset link sent successfully');
      } else {
        throw new Error('Failed to send password reset link');
      }
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message);
      } else {
        setError(error.message);
      }
    }
  }, [username, axiosInstance]);

  const handleRegister = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/auth/register', {
        username,
        email: username,
        password,
        role,
      });

      if (response.data) {
        alert('Registration successful');
      } else {
        throw new Error('Failed to register');
      }
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message);
      } else {
        setError(error.message);
      }
    }
  }, [username, password, role, axiosInstance]);

  useEffect(() => {
    const fetchLoginAttempts = async () => {
      try {
        const response = await axiosInstance.post('/api/auth/login-attempt', {
          username,
          password,
        });

        if (response.data) {
          const { attempt, locked } = response.data;
          setLoginAttempts(attempt);
          setIsAccountLocked(locked);
        } else {
          throw new Error('Failed to fetch login attempts');
        }
      } catch (error) {
        if (error.response) {
          setError(error.response.data.message);
        } else {
          setError(error.message);
        }
      }
    };

    fetchLoginAttempts();
  }, [username, password, axiosInstance]);

  return (
    <div className="login-page">
      <h1>Login Page</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {loading && <p>Loading...</p>}
      <form onSubmit={handleLogin}>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={handleUsernameChange}
            required
            aria-required="true"
            aria-label="Username"
          />
        </label>
        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={handlePasswordChange}
            required
            aria-required="true"
            aria-label="Password"
          />
        </label>
        <label>
          Role:
          <select value={role} onChange={handleRoleChange}>
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
          </select>
        </label>
        <label>
          Remember me:
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={handleRememberMeChange}
          />
        </label>
        <button type="submit" disabled={loading}>
          Login
        </button>
      </form>
      <p>
        <a href="#" onClick={handleForgotPassword}>
          Forgot password?
        </a>
      </p>
      <p>
        <a href="#" onClick={handleRegister}>
          Register
        </a>
      </p>
      {isAccountLocked && (
        <p>
          Account locked due to excessive login attempts. Please try again after
          some time.
        </p>
      )}
    </div>
  );
}

export default LoginPage;
