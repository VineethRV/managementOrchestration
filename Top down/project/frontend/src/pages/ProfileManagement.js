import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} UserProfile
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {string} role
 * @property {string} picture
 */

/**
 * @typedef {Object} ProfileUpdate
 * @property {string} name
 * @property {string} email
 */

/**
 * @typedef {Object} PasswordChange
 * @property {string} old_password
 * @property {string} new_password
 * @property {string} confirm_password
 */

/**
 * ProfileManagement component
 * @returns {JSX.Element}
 */
const ProfileManagement = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [profileUpdate, setProfileUpdate] = useState({});
  const [passwordChange, setPasswordChange] = useState({});
  const [profilePicture, setProfilePicture] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  const axiosInstance = useMemo(() => {
    const instance = axios.create({
      baseURL: 'http://localhost:5000',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
    return instance;
  }, []);

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/profile');
      setUserProfile(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const handleProfileUpdateChange = (event) => {
    setProfileUpdate({ ...profileUpdate, [event.target.name]: event.target.value });
  };

  const handlePasswordChangeChange = (event) => {
    setPasswordChange({ ...passwordChange, [event.target.name]: event.target.value });
  };

  const handleProfilePictureChange = (event) => {
    setProfilePicture(event.target.files[0]);
  };

  const validateProfileUpdate = async (profileUpdate) => {
    try {
      const response = await axiosInstance.post('/api/profile/validate', profileUpdate);
      if (!response.data.valid) {
        setValidationErrors(response.data.errors);
      } else {
        setValidationErrors({});
      }
      return response.data.valid;
    } catch (error) {
      setError(error.message);
      return false;
    }
  };

  const handleProfileUpdateSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      if (await validateProfileUpdate(profileUpdate)) {
        const response = await axiosInstance.put('/api/profile', profileUpdate);
        setUserProfile(response.data.updated_profile);
        setSuccess(response.data.message);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChangeSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await axiosInstance.post('/api/profile/password', passwordChange);
      setSuccess(response.data.message);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProfilePictureUpload = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('picture', profilePicture);
      const response = await axiosInstance.post('/api/profile/picture', formData);
      setUserProfile({ ...userProfile, picture: response.data.picture_url });
      setSuccess(response.data.message);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!userProfile) {
    return <div>No user profile found</div>;
  }

  return (
    <div>
      <h1>Profile Management</h1>
      <form onSubmit={handleProfileUpdateSubmit}>
        <label>
          Name:
          <input
            type="text"
            name="name"
            value={profileUpdate.name || userProfile.name}
            onChange={handleProfileUpdateChange}
          />
          {validationErrors.name && <div>{validationErrors.name}</div>}
        </label>
        <br />
        <label>
          Email:
          <input
            type="email"
            name="email"
            value={profileUpdate.email || userProfile.email}
            onChange={handleProfileUpdateChange}
          />
          {validationErrors.email && <div>{validationErrors.email}</div>}
        </label>
        <br />
        <button type="submit">Update Profile</button>
      </form>
      <form onSubmit={handlePasswordChangeSubmit}>
        <label>
          Old Password:
          <input
            type="password"
            name="old_password"
            value={passwordChange.old_password}
            onChange={handlePasswordChangeChange}
          />
        </label>
        <br />
        <label>
          New Password:
          <input
            type="password"
            name="new_password"
            value={passwordChange.new_password}
            onChange={handlePasswordChangeChange}
          />
        </label>
        <br />
        <label>
          Confirm Password:
          <input
            type="password"
            name="confirm_password"
            value={passwordChange.confirm_password}
            onChange={handlePasswordChangeChange}
          />
        </label>
        <br />
        <button type="submit">Change Password</button>
      </form>
      <form onSubmit={handleProfilePictureUpload}>
        <label>
          Profile Picture:
          <input
            type="file"
            name="picture"
            onChange={handleProfilePictureChange}
          />
        </label>
        <br />
        <button type="submit">Upload Profile Picture</button>
      </form>
      {success && <div>{success}</div>}
    </div>
  );
};

export default ProfileManagement;
