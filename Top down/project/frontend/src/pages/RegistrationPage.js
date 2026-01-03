import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} RegistrationFormProps
 * @property {function} onRegisterSuccess
 * @property {function} onCancel
 */

/**
 * @param {RegistrationFormProps} props
 * @returns {JSX.Element}
 */
function RegistrationForm({ onRegisterSuccess, onCancel }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('');
  const [name, setName] = useState('');
  const [termsAndConditions, setTermsAndConditions] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [roles, setRoles] = useState([]);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const validateEmail = useCallback(async (email) => {
    try {
      const response = await axiosInstance.get('/api/validate-email', {
        params: { email },
      });
      return response.data.isAvailable;
    } catch (error) {
      console.error(error);
      return false;
    }
  }, [axiosInstance]);

  const validateUsername = useCallback(async (username) => {
    try {
      const response = await axiosInstance.get('/api/validate-username', {
        params: { username },
      });
      return response.data.isAvailable;
    } catch (error) {
      console.error(error);
      return false;
    }
  }, [axiosInstance]);

  const checkPasswordStrength = useCallback(async (password) => {
    try {
      const response = await axiosInstance.post('/api/check-password-strength', {
        password,
      });
      return response.data;
    } catch (error) {
      console.error(error);
      return null;
    }
  }, [axiosInstance]);

  const getRoles = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/roles');
      setRoles(response.data);
    } catch (error) {
      console.error(error);
    }
  }, [axiosInstance]);

  const getTermsAndConditions = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/terms-and-conditions');
      // setTermsAndConditions(response.data.terms_and_conditions);
    } catch (error) {
      console.error(error);
    }
  }, [axiosInstance]);

  useEffect(() => {
    getRoles();
    getTermsAndConditions();
  }, [getRoles, getTermsAndConditions]);

  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
    checkPasswordStrength(event.target.value).then((strength) => {
      setPasswordStrength(strength);
    });
  };

  const handleConfirmPasswordChange = (event) => {
    setConfirmPassword(event.target.value);
  };

  const handleRoleChange = (event) => {
    setRole(event.target.value);
  };

  const handleNameChange = (event) => {
    setName(event.target.value);
  };

  const handleTermsAndConditionsChange = (event) => {
    setTermsAndConditions(event.target.checked);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!username || !email || !password || !confirmPassword || !role || !name) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!termsAndConditions) {
      setError('Please agree to the terms and conditions');
      return;
    }
    validateEmail(email).then((isAvailable) => {
      if (!isAvailable) {
        setError('Email is already in use');
        return;
      }
      validateUsername(username).then((isAvailable) => {
        if (!isAvailable) {
          setError('Username is already in use');
          return;
        }
        const registrationData = {
          username,
          email,
          password,
          role,
          name,
        };
        axiosInstance
          .post('/api/register', registrationData)
          .then((response) => {
            onRegisterSuccess(response.data);
            setSuccess('Registration successful');
          })
          .catch((error) => {
            setError(error.message);
          });
      });
    });
  };

  const handleCancel = () => {
    onCancel();
  };

  return (
    <div>
      <h1>Registration Form</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label>
            Username:
            <input
              type="text"
              value={username}
              onChange={handleUsernameChange}
              required
            />
          </label>
          <br />
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={handleEmailChange}
              required
            />
          </label>
          <br />
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={handlePasswordChange}
              required
            />
          </label>
          {passwordStrength && (
            <p>
              Password strength: {passwordStrength.strength} ({passwordStrength.score})
            </p>
          )}
          <br />
          <label>
            Confirm Password:
            <input
              type="password"
              value={confirmPassword}
              onChange={handleConfirmPasswordChange}
              required
            />
          </label>
          <br />
          <label>
            Role:
            <select value={role} onChange={handleRoleChange}>
              <option value="">Select a role</option>
              {roles.map((role) => (
                <option key={role.id} value={role.name}>
                  {role.name}
                </option>
              ))}
            </select>
          </label>
          <br />
          <label>
            Name:
            <input
              type="text"
              value={name}
              onChange={handleNameChange}
              required
            />
          </label>
          <br />
          <label>
            <input
              type="checkbox"
              checked={termsAndConditions}
              onChange={handleTermsAndConditionsChange}
              required
            />
            I agree to the terms and conditions
          </label>
          <br />
          <button type="submit">Register</button>
          <button type="button" onClick={handleCancel}>
            Cancel
          </button>
        </form>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
      <p>
        Already have an account? <a href="/login">Login</a>
      </p>
    </div>
  );
}

export default RegistrationForm;
