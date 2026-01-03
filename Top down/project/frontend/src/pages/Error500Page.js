import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} ErrorDetails
 * @property {number} errorId
 * @property {string} errorCode
 * @property {string} errorMessage
 * @property {string} errorStack
 * @property {boolean} reported
 */

/**
 * @typedef {Object} ReportIssueRequest
 * @property {string} description
 * @property {string} stepsToReproduce
 */

/**
 * @param {Object} props
 * @returns {JSX.Element}
 */
function Error500Page() {
  const [errorDetails, setErrorDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportIssue, setReportIssue] = useState(false);
  const [reportIssueRequest, setReportIssueRequest] = useState({
    description: '',
    stepsToReproduce: '',
  });
  const [reportIssueError, setReportIssueError] = useState(null);

  const fetchErrorDetails = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/errors/500');
      setErrorDetails(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchErrorDetails();
  }, [fetchErrorDetails]);

  const handleReportIssue = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(`http://localhost:5000/api/errors/${errorDetails.errorId}/report`, reportIssueRequest);
      setReportIssue(true);
    } catch (error) {
      setReportIssueError(error.message);
    }
  }, [errorDetails, reportIssueRequest]);

  const handleRefresh = useCallback(() => {
    window.location.reload();
  }, []);

  if (loading) {
    return (
      <div className="error-page">
        <h1>Loading...</h1>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-page">
        <h1>Error: {error}</h1>
      </div>
    );
  }

  return (
    <div className="error-page">
      <h1>Internal Server Error (500)</h1>
      <p>Error Code: {errorDetails.errorCode}</p>
      <p>Error Message: {errorDetails.errorMessage}</p>
      <button onClick={handleRefresh}>Refresh Page</button>
      <button onClick={() => window.history.back()}>Go Back</button>
      <p>
        If the issue persists, please{' '}
        <a href="mailto:support@example.com">contact our support team</a> for assistance.
      </p>
      {!reportIssue && (
        <form onSubmit={handleReportIssue}>
          <h2>Report Issue</h2>
          <label>
            Description:
            <textarea
              value={reportIssueRequest.description}
              onChange={(event) => setReportIssueRequest({ ...reportIssueRequest, description: event.target.value })}
            />
          </label>
          <label>
            Steps to Reproduce:
            <textarea
              value={reportIssueRequest.stepsToReproduce}
              onChange={(event) => setReportIssueRequest({ ...reportIssueRequest, stepsToReproduce: event.target.value })}
            />
          </label>
          <button type="submit">Report Issue</button>
          {reportIssueError && <p style={{ color: 'red' }}>{reportIssueError}</p>}
        </form>
      )}
      {reportIssue && <p>Issue reported successfully.</p>}
    </div>
  );
}

export default Error500Page;
