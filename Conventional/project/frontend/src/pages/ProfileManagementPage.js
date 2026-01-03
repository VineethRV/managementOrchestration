import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

/**
 * Profile Management Page Component
 * 
 * This component allows users to view and update their profile details.
 * 
 * @returns {JSX.Element} Profile Management Page
 */
const ProfileManagementPage = () => {
  // State to store user profile details
  const [profileDetails, setProfileDetails] = useState({
    username: '',
    role: '',
  });

  // State to store loading status
  const [isLoading, setIsLoading] = useState(false);

  // State to store error message
  const [error, setError] = useState(null);

  // Use navigate hook from react-router-dom
  const navigate = useNavigate();

  // Use useForm hook from react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      username: '',
      role: '',
    },
  });

  // Use callback to fetch user profile details
  const fetchProfileDetails = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('http://localhost:5000/user/profile', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setProfileDetails(response.data.profile_details);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Use effect to fetch user profile details on component mount
  useEffect(() => {
    fetchProfileDetails();
  }, [fetchProfileDetails]);

  // Use callback to update user profile details
  const updateProfileDetails = useCallback(async (data) => {
    try {
      setIsLoading(true);
      const response = await axios.put('http://localhost:5000/user/profile', data, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setProfileDetails(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle form submission
  const onSubmit = async (data) => {
    await updateProfileDetails(data);
  };

  // Render component
  return (
    <main>
      <h1>Profile Management Page</h1>
      {isLoading ? (
        <p>Loading...</p>
      ) : error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <label>
            Username:
            <input
              type="text"
              {...register('username', {
                required: 'Username is required',
              })}
              defaultValue={profileDetails.username}
            />
            {errors.username && <p style={{ color: 'red' }}>{errors.username.message}</p>}
          </label>
          <label>
            Role:
            <input
              type="text"
              {...register('role', {
                required: 'Role is required',
              })}
              defaultValue={profileDetails.role}
              readOnly
            />
            {errors.role && <p style={{ color: 'red' }}>{errors.role.message}</p>}
          </label>
          <button type="submit">Update Profile</button>
        </form>
      )}
    </main>
  );
};

export default ProfileManagementPage;
