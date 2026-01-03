import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} PasswordRecoveryProps
 * @property {string} clientUrl - The URL of the client application to redirect the user after password recovery
 */

/**
 * @param {PasswordRecoveryProps} props
 * @returns {JSX.Element}
 */
const PasswordRecovery = ({ clientUrl }) => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  const validateForm = useCallback(() => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const isValid = emailRegex.test(usernameOrEmail) || usernameOrEmail.length > 3;
    setIsFormValid(isValid);
  }, [usernameOrEmail]);

  const handleUsernameOrEmailChange = useCallback((event) => {
    setUsernameOrEmail(event.target.value);
    validateForm();
  }, [validateForm]);

  const handleRecoverPassword = useCallback(async () => {
    if (!isFormValid) return;
    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const response = await axios.post('http://localhost:5000/api/password-recovery/send-email', {
        username_or_email: usernameOrEmail,
        client_url: clientUrl,
      });
      if (response.data.success) {
        setSuccessMessage('Password recovery email sent successfully');
      } else {
        setErrorMessage(response.data.message);
      }
    } catch (error) {
      setErrorMessage('Error sending password recovery email');
    } finally {
      setLoading(false);
    }
  }, [isFormValid, usernameOrEmail, clientUrl]);

  const handleResendEmail = useCallback(async () => {
    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const response = await axios.post('http://localhost:5000/api/password-recovery/resend-email', {
        username_or_email: usernameOrEmail,
        client_url: clientUrl,
      });
      if (response.data.success) {
        setSuccessMessage('Password recovery email resent successfully');
      } else {
        setErrorMessage(response.data.message);
      }
    } catch (error) {
      setErrorMessage('Error resending password recovery email');
    } finally {
      setLoading(false);
    }
  }, [usernameOrEmail, clientUrl]);

  return (
    <div className="password-recovery">
      <h1>Password Recovery</h1>
      <form>
        <label htmlFor="username-or-email">Username or Email:</label>
        <input
          type="text"
          id="username-or-email"
          value={usernameOrEmail}
          onChange={handleUsernameOrEmailChange}
          aria-required="true"
          aria-invalid={!isFormValid}
        />
        {isFormValid ? null : (
          <div role="alert" aria-live="assertive">
            Please enter a valid username or email address
          </div>
        )}
        <button type="button" onClick={handleRecoverPassword} disabled={loading || !isFormValid}>
          {loading ? 'Sending...' : 'Recover Password'}
        </button>
        {successMessage && (
          <div role="alert" aria-live="assertive">
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div role="alert" aria-live="assertive">
            {errorMessage}
          </div>
        )}
        <button type="button" onClick={handleResendEmail} disabled={loading}>
          Resend Email
        </button>
      </form>
      <p>
        <a href="/login">Return to Login Page</a>
      </p>
    </div>
  );
};

export default PasswordRecovery;
