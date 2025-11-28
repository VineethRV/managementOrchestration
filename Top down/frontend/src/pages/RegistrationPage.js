import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * RegistrationPage component
 * @returns {JSX.Element} Registration page component
 */
const RegistrationPage = () => {
  // State to store registration form data
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAndConditions, setTermsAndConditions] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  // API base URL
  const apiBaseUrl = 'http://localhost:5000';

  // Function to handle form submission
  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    // Validate form data
    const formData = { username, email, password, confirmPassword };
    try {
      const response = await axios.post(`${apiBaseUrl}/api/registration/validate`, formData);
      if (response.data.valid) {
        // Create new user
        const createUserResponse = await axios.post(`${apiBaseUrl}/api/registration`, formData);
        if (createUserResponse.data.userId) {
          setRegistrationSuccess(true);
        } else {
          setErrors({ message: 'Failed to create user' });
        }
      } else {
        setErrors(response.data.errors);
      }
    } catch (error) {
      setErrors({ message: 'Error registering user' });
    }
  }, [username, email, password, confirmPassword, apiBaseUrl]);

  // Function to check username availability
  const checkUsernameAvailability = useCallback(async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/registration/username/${username}`);
      if (!response.data.available) {
        setErrors({ username: 'Username is not available' });
      }
    } catch (error) {
      setErrors({ username: 'Error checking username availability' });
    }
  }, [username, apiBaseUrl]);

  // Function to check email availability
  const checkEmailAvailability = useCallback(async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/registration/email/${email}`);
      if (!response.data.available) {
        setErrors({ email: 'Email is not available' });
      }
    } catch (error) {
      setErrors({ email: 'Error checking email availability' });
    }
  }, [email, apiBaseUrl]);

  // Effect to check username and email availability on input change
  useEffect(() => {
    if (username) {
      checkUsernameAvailability();
    }
    if (email) {
      checkEmailAvailability();
    }
  }, [username, email, checkUsernameAvailability, checkEmailAvailability]);

  // Function to handle terms and conditions checkbox change
  const handleTermsAndConditionsChange = useCallback((event) => {
    setTermsAndConditions(event.target.checked);
  }, []);

  // Function to handle login link click
  const handleLoginLinkClick = useCallback(async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/login`);
      window.location.href = response.data.redirect_url;
    } catch (error) {
      setErrors({ message: 'Error redirecting to login page' });
    }
  }, [apiBaseUrl]);

  // Render registration form
  return (
    <div className="registration-page">
      <h1>Registration Page</h1>
      {registrationSuccess ? (
        <p>Registration successful! Please login to continue.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label>
            Username:
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter username"
              aria-required="true"
              aria-invalid={errors.username ? 'true' : 'false'}
            />
            {errors.username && <span aria-live="assertive">{errors.username}</span>}
          </label>
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter email"
              aria-required="true"
              aria-invalid={errors.email ? 'true' : 'false'}
            />
            {errors.email && <span aria-live="assertive">{errors.email}</span>}
          </label>
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              aria-required="true"
              aria-invalid={errors.password ? 'true' : 'false'}
            />
            {errors.password && <span aria-live="assertive">{errors.password}</span>}
          </label>
          <label>
            Confirm Password:
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Confirm password"
              aria-required="true"
              aria-invalid={errors.confirmPassword ? 'true' : 'false'}
            />
            {errors.confirmPassword && <span aria-live="assertive">{errors.confirmPassword}</span>}
          </label>
          <label>
            Terms and Conditions:
            <input
              type="checkbox"
              checked={termsAndConditions}
              onChange={handleTermsAndConditionsChange}
              aria-required="true"
            />
            <a href={`${apiBaseUrl}/api/terms-and-conditions`} target="_blank" rel="noopener noreferrer">
              View Terms and Conditions
            </a>
          </label>
          <button type="submit" disabled={loading || !termsAndConditions}>
            Register
          </button>
          {loading && <p>Loading...</p>}
          {errors.message && <span aria-live="assertive">{errors.message}</span>}
        </form>
      )}
      <p>
        Already have an account?{' '}
        <a href="#" onClick={handleLoginLinkClick}>
          Login
        </a>
      </p>
    </div>
  );
};

export default RegistrationPage;
