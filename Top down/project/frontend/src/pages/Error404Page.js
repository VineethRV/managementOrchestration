import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} Error404PageProps
 * @property {string} [homepageLink]
 * @property {string} [dashboardLink]
 * @property {string} [contactLink]
 * @property {string} [previousPageLink]
 */

/**
 * @param {Error404PageProps} props
 * @returns {JSX.Element}
 */
const Error404Page = () => {
  const [homepageLink, setHomepageLink] = useState('');
  const [dashboardLink, setDashboardLink] = useState('');
  const [contactLink, setContactLink] = useState('');
  const [previousPageLink, setPreviousPageLink] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [issueType, setIssueType] = useState('');
  const [issueDescription, setIssueDescription] = useState('');

  const getHomepageLink = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/homepage');
      setHomepageLink(response.data.homepageLink);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getDashboardLink = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/dashboard');
      setDashboardLink(response.data.link);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getContactLink = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/contact');
      setContactLink(response.data.contact_link);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getPreviousPageLink = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/previous-page');
      setPreviousPageLink(response.data.previous_page_link);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const handleSearch = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axios.get('http://localhost:5000/api/search', {
        params: {
          query: searchQuery,
          type: 'user',
          limit: 10,
          offset: 0,
        },
      });
      setSearchResults(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [searchQuery]);

  const handleReportIssue = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/report-issue', {
        issue_type: issueType,
        description: issueDescription,
      });
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [issueType, issueDescription]);

  useEffect(() => {
    getHomepageLink();
    getDashboardLink();
    getContactLink();
    getPreviousPageLink();
  }, [getHomepageLink, getDashboardLink, getContactLink, getPreviousPageLink]);

  return (
    <div className="error-404-page">
      <h1>Error 404: Page Not Found</h1>
      <p>
        The page you are looking for does not exist or has been moved. Please try
        searching for what you are looking for or visit our homepage.
      </p>
      <form onSubmit={handleSearch}>
        <label>
          Search:
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search for users or roles"
          />
        </label>
        <button type="submit">Search</button>
      </form>
      {searchResults.length > 0 && (
        <ul>
          {searchResults.map((result) => (
            <li key={result.id}>{result.name}</li>
          ))}
        </ul>
      )}
      <p>
        <a href={homepageLink}>Visit our homepage</a> or{' '}
        <a href={dashboardLink}>visit our dashboard</a>
      </p>
      <p>
        <a href={previousPageLink}>Back to previous page</a>
      </p>
      <p>
        If you are experiencing issues, please{' '}
        <a href={contactLink}>contact our support team</a>
      </p>
      <form onSubmit={handleReportIssue}>
        <label>
          Report an issue:
          <select value={issueType} onChange={(event) => setIssueType(event.target.value)}>
            <option value="">Select an issue type</option>
            <option value="technical">Technical issue</option>
            <option value="attendance">Attendance issue</option>
            <option value="other">Other issue</option>
          </select>
        </label>
        <label>
          Description:
          <textarea
            value={issueDescription}
            onChange={(event) => setIssueDescription(event.target.value)}
          />
        </label>
        <button type="submit">Report issue</button>
      </form>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default Error404Page;
