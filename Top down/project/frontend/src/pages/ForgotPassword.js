import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * Forgot Password component
 * 
 * @returns {JSX.Element} Forgot Password component
 */
const ForgotPassword = () => {
  // State to store the username or email
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  // State to store the error message
  const [error, setError] = useState(null);
  // State to store the loading state
  const [isLoading, setIsLoading] = useState(false);
  // State to store the success message
  const [success, setSuccess] = useState(null);

  // Function to handle form submission
  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate user input
      const response = await axios.post('http://localhost:5000/api/validate-credentials', {
        username_or_email: usernameOrEmail,
      });

      if (!response.data.status) {
        setError(response.data.message);
        setIsLoading(false);
        return;
      }

      // Initiate password recovery process
      const recoveryResponse = await axios.post('http://localhost:5000/api/forgot-password', {
        email: usernameOrEmail,
      });

      if (recoveryResponse.data.status === 'success') {
        setSuccess(recoveryResponse.data.message);
      } else {
        setError(recoveryResponse.data.message);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [usernameOrEmail]);

  // Function to handle input change
  const handleInputChange = useCallback((event) => {
    setUsernameOrEmail(event.target.value);
  }, []);

  // Render the component
  return (
    <div className="forgot-password">
      <h1>Forgot Password</h1>
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="usernameOrEmail">Username or Email:</label>
          <input
            type="text"
            id="usernameOrEmail"
            value={usernameOrEmail}
            onChange={handleInputChange}
            placeholder="Enter your username or email"
          />
          {error ? <p style={{ color: 'red' }}>{error}</p> : null}
          {success ? <p style={{ color: 'green' }}>{success}</p> : null}
          <button type="submit">Submit</button>
        </form>
      )}
      <p>
        <a href="/login">Back to Login</a>
      </p>
    </div>
  );
};

export default ForgotPassword;
