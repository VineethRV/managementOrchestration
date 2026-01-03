import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} ApplicationInfo
 * @property {string} application_name
 * @property {string} application_logo
 */

/**
 * @typedef {Object} NavigationMenu
 * @property {Array} menu_items
 */

/**
 * @typedef {Object} UserProfile
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {string} role
 * @property {string} created_at
 */

/**
 * @typedef {Object} AccountSettings
 * @property {Object} notification_preferences
 * @property {string} theme
 * @property {string} language
 */

/**
 * @typedef {Object} NotificationPreferences
 * @property {boolean} attendance_reminders
 * @property {boolean} low_attendance_warnings
 * @property {boolean} absence_notifications
 */

/**
 * @typedef {Object} AttendanceSettings
 * @property {number} mark_attendance_time_limit
 * @property {number} attendance_grace_period
 * @property {number} max_allowed_absences
 */

/**
 * @typedef {Object} SystemDefaults
 * @property {string} default_attendance_marking_time
 * @property {Array<string>} default_attendance_marking_days
 * @property {number} default_attendance_grace_period
 * @property {string} default_attendance_notification_frequency
 * @property {Array<string>} default_attendance_notification_recipients
 */

/**
 * @typedef {Object} Settings
 * @property {string} key
 * @property {string} value
 */

/**
 * Settings component
 * @returns {JSX.Element}
 */
function Settings() {
  const [applicationInfo, setApplicationInfo] = useState({});
  const [navigationMenu, setNavigationMenu] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [userProfile, setUserProfile] = useState({});
  const [accountSettings, setAccountSettings] = useState({});
  const [notificationPreferences, setNotificationPreferences] = useState({});
  const [attendanceSettings, setAttendanceSettings] = useState({});
  const [systemDefaults, setSystemDefaults] = useState({});
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const fetchApplicationInfo = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/app-info');
      setApplicationInfo(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchNavigationMenu = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/navigation-menu');
      setNavigationMenu(response.data.menu_items);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleSearch = useCallback(async (query) => {
    try {
      const response = await axiosInstance.get('/api/settings/search', {
        params: { key: query },
      });
      setSearchResults(response.data.settings);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/user-profile');
      setUserProfile(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateUserProfile = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/user-profile', data);
      setUserProfile(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const changePassword = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/user-profile/password', data);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchAccountSettings = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/account-settings');
      setAccountSettings(response.data.data.account_settings);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateAccountSettings = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/account-settings', data);
      setAccountSettings(response.data.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchNotificationPreferences = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/notification-preferences');
      setNotificationPreferences(response.data.notification_preferences);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateNotificationPreferences = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/notification-preferences', data);
      setNotificationPreferences(response.data.notification_preferences);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchAttendanceSettings = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/attendance-settings');
      setAttendanceSettings(response.data.attendance_settings);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateAttendanceSettings = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/attendance-settings', data);
      setAttendanceSettings(response.data.attendance_settings);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchSystemDefaults = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/system-defaults');
      setSystemDefaults(response.data.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateSystemDefaults = useCallback(async (data) => {
    try {
      const response = await axiosInstance.put('/api/system-defaults', data);
      setSystemDefaults(response.data.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const saveSettings = useCallback(async (data) => {
    try {
      const response = await axiosInstance.post('/api/settings/save', data);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const validateSettings = useCallback(async (data) => {
    try {
      const response = await axiosInstance.post('/api/settings/validate', data);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const resetSettings = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/settings/reset');
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    fetchApplicationInfo();
    fetchNavigationMenu();
    fetchUserProfile();
    fetchAccountSettings();
    fetchNotificationPreferences();
    fetchAttendanceSettings();
    fetchSystemDefaults();
  }, [
    fetchApplicationInfo,
    fetchNavigationMenu,
    fetchUserProfile,
    fetchAccountSettings,
    fetchNotificationPreferences,
    fetchAttendanceSettings,
    fetchSystemDefaults,
  ]);

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    handleSearch(searchQuery);
  };

  const handleUserProfileUpdate = (event) => {
    event.preventDefault();
    const data = {
      name: event.target.name.value,
      email: event.target.email.value,
    };
    updateUserProfile(data);
  };

  const handlePasswordChange = (event) => {
    event.preventDefault();
    const data = {
      current_password: event.target.current_password.value,
      new_password: event.target.new_password.value,
      confirm_password: event.target.confirm_password.value,
    };
    changePassword(data);
  };

  const handleAccountSettingsUpdate = (event) => {
    event.preventDefault();
    const data = {
      notification_preferences: {
        email_notifications: event.target.email_notifications.checked,
        sms_notifications: event.target.sms_notifications.checked,
      },
      theme: event.target.theme.value,
      language: event.target.language.value,
    };
    updateAccountSettings(data);
  };

  const handleNotificationPreferencesUpdate = (event) => {
    event.preventDefault();
    const data = {
      attendance_reminders: event.target.attendance_reminders.checked,
      low_attendance_warnings: event.target.low_attendance_warnings.checked,
      absence_notifications: event.target.absence_notifications.checked,
    };
    updateNotificationPreferences(data);
  };

  const handleAttendanceSettingsUpdate = (event) => {
    event.preventDefault();
    const data = {
      mark_attendance_time_limit: event.target.mark_attendance_time_limit.value,
      attendance_grace_period: event.target.attendance_grace_period.value,
      max_allowed_absences: event.target.max_allowed_absences.value,
    };
    updateAttendanceSettings(data);
  };

  const handleSystemDefaultsUpdate = (event) => {
    event.preventDefault();
    const data = {
      default_attendance_marking_time: event.target.default_attendance_marking_time.value,
      default_attendance_marking_days: event.target.default_attendance_marking_days.value,
      default_attendance_grace_period: event.target.default_attendance_grace_period.value,
      default_attendance_notification_frequency: event.target.default_attendance_notification_frequency.value,
      default_attendance_notification_recipients: event.target.default_attendance_notification_recipients.value,
    };
    updateSystemDefaults(data);
  };

  const handleSaveSettings = (event) => {
    event.preventDefault();
    const data = {
      settings: [
        {
          key: 'attendance',
          value: 'daily',
        },
      ],
    };
    saveSettings(data);
  };

  const handleValidateSettings = (event) => {
    event.preventDefault();
    const data = {
      settings: [
        {
          key: 'attendance',
          value: 'daily',
        },
      ],
    };
    validateSettings(data);
  };

  const handleResetSettings = (event) => {
    event.preventDefault();
    resetSettings();
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Settings</h1>
      <img src={applicationInfo.application_logo} alt={applicationInfo.application_name} />
      <nav>
        <ul>
          {navigationMenu.map((menuItem) => (
            <li key={menuItem.id}>
              <a href={menuItem.url}>
                {menuItem.name}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <form onSubmit={handleSearchSubmit}>
        <input
          type="search"
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search settings"
        />
        <button type="submit">Search</button>
      </form>
      <ul>
        {searchResults.map((result) => (
          <li key={result.key}>
            {result.key}: {result.value}
          </li>
        ))}
      </ul>
      <h2>User Profile</h2>
      <form onSubmit={handleUserProfileUpdate}>
        <label>
          Name:
          <input type="text" name="name" defaultValue={userProfile.name} />
        </label>
        <label>
          Email:
          <input type="email" name="email" defaultValue={userProfile.email} />
        </label>
        <button type="submit">Update Profile</button>
      </form>
      <form onSubmit={handlePasswordChange}>
        <label>
          Current Password:
          <input type="password" name="current_password" />
        </label>
        <label>
          New Password:
          <input type="password" name="new_password" />
        </label>
        <label>
          Confirm Password:
          <input type="password" name="confirm_password" />
        </label>
        <button type="submit">Change Password</button>
      </form>
      <h2>Account Settings</h2>
      <form onSubmit={handleAccountSettingsUpdate}>
        <label>
          Email Notifications:
          <input
            type="checkbox"
            name="email_notifications"
            defaultChecked={accountSettings.notification_preferences?.email_notifications}
          />
        </label>
        <label>
          SMS Notifications:
          <input
            type="checkbox"
            name="sms_notifications"
            defaultChecked={accountSettings.notification_preferences?.sms_notifications}
          />
        </label>
        <label>
          Theme:
          <select name="theme" defaultValue={accountSettings.theme}>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
        <label>
          Language:
          <select name="language" defaultValue={accountSettings.language}>
            <option value="en">English</option>
            <option value="fr">French</option>
          </select>
        </label>
        <button type="submit">Update Account Settings</button>
      </form>
      <h2>Notification Preferences</h2>
      <form onSubmit={handleNotificationPreferencesUpdate}>
        <label>
          Attendance Reminders:
          <input
            type="checkbox"
            name="attendance_reminders"
            defaultChecked={notificationPreferences.attendance_reminders}
          />
        </label>
        <label>
          Low Attendance Warnings:
          <input
            type="checkbox"
            name="low_attendance_warnings"
            defaultChecked={notificationPreferences.low_attendance_warnings}
          />
        </label>
        <label>
          Absence Notifications:
          <input
            type="checkbox"
            name="absence_notifications"
            defaultChecked={notificationPreferences.absence_notifications}
          />
        </label>
        <button type="submit">Update Notification Preferences</button>
      </form>
      <h2>Attendance Settings</h2>
      <form onSubmit={handleAttendanceSettingsUpdate}>
        <label>
          Mark Attendance Time Limit:
          <input
            type="number"
            name="mark_attendance_time_limit"
            defaultValue={attendanceSettings.mark_attendance_time_limit}
          />
        </label>
        <label>
          Attendance Grace Period:
          <input
            type="number"
            name="attendance_grace_period"
            defaultValue={attendanceSettings.attendance_grace_period}
          />
        </label>
        <label>
          Max Allowed Absences:
          <input
            type="number"
            name="max_allowed_absences"
            defaultValue={attendanceSettings.max_allowed_absences}
          />
        </label>
        <button type="submit">Update Attendance Settings</button>
      </form>
      <h2>System Defaults</h2>
      <form onSubmit={handleSystemDefaultsUpdate}>
        <label>
          Default Attendance Marking Time:
          <input
            type="time"
            name="default_attendance_marking_time"
            defaultValue={systemDefaults.default_attendance_marking_time}
          />
        </label>
        <label>
          Default Attendance Marking Days:
          <select
            name="default_attendance_marking_days"
            multiple
            defaultValue={systemDefaults.default_attendance_marking_days}
          >
            <option value="Monday">Monday</option>
            <option value="Tuesday">Tuesday</option>
            <option value="Wednesday">Wednesday</option>
            <option value="Thursday">Thursday</option>
            <option value="Friday">Friday</option>
          </select>
        </label>
        <label>
          Default Attendance Grace Period:
          <input
            type="number"
            name="default_attendance_grace_period"
            defaultValue={systemDefaults.default_attendance_grace_period}
          />
        </label>
        <label>
          Default Attendance Notification Frequency:
          <select
            name="default_attendance_notification_frequency"
            defaultValue={systemDefaults.default_attendance_notification_frequency}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </label>
        <label>
          Default Attendance Notification Recipients:
          <input
            type="text"
            name="default_attendance_notification_recipients"
            defaultValue={systemDefaults.default_attendance_notification_recipients}
          />
        </label>
        <button type="submit">Update System Defaults</button>
      </form>
      <button onClick={handleSaveSettings}>Save Settings</button>
      <button onClick={handleValidateSettings}>Validate Settings</button>
      <button onClick={handleResetSettings}>Reset Settings</button>
    </div>
  );
}

export default Settings;
