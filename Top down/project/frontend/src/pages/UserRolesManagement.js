import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} UserRole
 * @property {number} roleId
 * @property {string} roleName
 * @property {Object[]} permissions
 * @property {number} permissionId
 * @property {string} permissionName
 */

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} username
 * @property {string} email
 * @property {Object[]} roles
 * @property {number} id
 * @property {string} name
 */

/**
 * UserRolesManagement component
 * @returns {JSX.Element}
 */
const UserRolesManagement = () => {
  const [userRoles, setUserRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [newRole, setNewRole] = useState({ roleName: '', permissions: [] });
  const [editedRole, setEditedRole] = useState({ roleId: null, roleName: '', permissions: [] });
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [sortedUsers, setSortedUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userCount, setUserCount] = useState(0);
  const [roleCount, setRoleCount] = useState({ student: 0, teacher: 0 });

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchUserRoles = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/user-roles');
      setUserRoles(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchUsers = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/users');
      setUsers(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchUserCountAndRoleCount = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/stats');
      setUserCount(response.data.user_count);
      setRoleCount(response.data.role_count);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    fetchUserRoles();
    fetchUsers();
    fetchUserCountAndRoleCount();
  }, [fetchUserRoles, fetchUsers, fetchUserCountAndRoleCount]);

  const handleCreateRole = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.post('/api/user-roles', newRole);
      setUserRoles((prevUserRoles) => [...prevUserRoles, response.data]);
      setNewRole({ roleName: '', permissions: [] });
    } catch (error) {
      setError(error.message);
    }
  }, [newRole, axiosInstance]);

  const handleEditRole = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.put(`/api/user-roles/${editedRole.roleId}`, editedRole);
      setUserRoles((prevUserRoles) =>
        prevUserRoles.map((userRole) => (userRole.roleId === editedRole.roleId ? response.data : userRole))
      );
      setEditedRole({ roleId: null, roleName: '', permissions: [] });
    } catch (error) {
      setError(error.message);
    }
  }, [editedRole, axiosInstance]);

  const handleDeleteRole = useCallback(async (roleId) => {
    try {
      await axiosInstance.delete(`/api/user-roles/${roleId}`);
      setUserRoles((prevUserRoles) => prevUserRoles.filter((userRole) => userRole.roleId !== roleId));
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleAssignRole = useCallback(async (userId, roleId) => {
    try {
      const response = await axiosInstance.post(`/api/users/${userId}/roles`, { roleId });
      setUsers((prevUsers) =>
        prevUsers.map((user) =>
          user.id === userId ? { ...user, roles: [...user.roles, response.data] } : user
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleUnassignRole = useCallback(async (userId, roleId) => {
    try {
      await axiosInstance.delete(`/api/users/${userId}/roles/${roleId}`);
      setUsers((prevUsers) =>
        prevUsers.map((user) =>
          user.id === userId
            ? { ...user, roles: user.roles.filter((role) => role.id !== roleId) }
            : user
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleSearch = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axiosInstance.get('/api/search', {
        params: { query: searchQuery, type: 'user' },
      });
      setFilteredUsers(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [searchQuery, axiosInstance]);

  const handleSort = useCallback(async (sort, order) => {
    try {
      const response = await axiosInstance.get('/api/users/sorted', {
        params: { sort, order },
      });
      setSortedUsers(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleFilter = useCallback(async (roleId) => {
    try {
      const response = await axiosInstance.get(`/api/users/by-role/${roleId}`);
      setFilteredUsers(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>User Roles Management</h1>
      <p>Total Users: {userCount}</p>
      <p>Total Roles: {roleCount.student + roleCount.teacher}</p>
      <h2>User Roles</h2>
      <ul>
        {userRoles.map((userRole) => (
          <li key={userRole.roleId}>
            {userRole.roleName}
            <button onClick={() => handleDeleteRole(userRole.roleId)}>Delete</button>
            <button
              onClick={() =>
                setEditedRole({ roleId: userRole.roleId, roleName: userRole.roleName, permissions: userRole.permissions })
              }
            >
              Edit
            </button>
          </li>
        ))}
      </ul>
      <h2>Create New Role</h2>
      <form onSubmit={handleCreateRole}>
        <label>
          Role Name:
          <input type="text" value={newRole.roleName} onChange={(event) => setNewRole({ ...newRole, roleName: event.target.value })} />
        </label>
        <label>
          Permissions:
          <input
            type="text"
            value={newRole.permissions.join(',')}
            onChange={(event) =>
              setNewRole({ ...newRole, permissions: event.target.value.split(',') })
            }
          />
        </label>
        <button type="submit">Create</button>
      </form>
      <h2>Edit Role</h2>
      {editedRole.roleId && (
        <form onSubmit={handleEditRole}>
          <label>
            Role Name:
            <input
              type="text"
              value={editedRole.roleName}
              onChange={(event) => setEditedRole({ ...editedRole, roleName: event.target.value })}
            />
          </label>
          <label>
            Permissions:
            <input
              type="text"
              value={editedRole.permissions.join(',')}
              onChange={(event) =>
                setEditedRole({ ...editedRole, permissions: event.target.value.split(',') })
              }
            />
          </label>
          <button type="submit">Edit</button>
        </form>
      )}
      <h2>Users</h2>
      <ul>
        {users.map((user) => (
          <li key={user.id}>
            {user.username}
            <ul>
              {user.roles.map((role) => (
                <li key={role.id}>
                  {role.name}
                  <button onClick={() => handleUnassignRole(user.id, role.id)}>Unassign</button>
                </li>
              ))}
            </ul>
            <select
              value=""
              onChange={(event) => handleAssignRole(user.id, event.target.value)}
            >
              <option value="">Select Role</option>
              {userRoles.map((userRole) => (
                <option key={userRole.roleId} value={userRole.roleId}>
                  {userRole.roleName}
                </option>
              ))}
            </select>
          </li>
        ))}
      </ul>
      <h2>Search</h2>
      <form onSubmit={handleSearch}>
        <label>
          Search Query:
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </label>
        <button type="submit">Search</button>
      </form>
      <h2>Filtered Users</h2>
      <ul>
        {filteredUsers.map((user) => (
          <li key={user.id}>
            {user.username}
          </li>
        ))}
      </ul>
      <h2>Sort</h2>
      <button onClick={() => handleSort('name', 'asc')}>Sort by Name (ASC)</button>
      <button onClick={() => handleSort('name', 'desc')}>Sort by Name (DESC)</button>
      <h2>Sorted Users</h2>
      <ul>
        {sortedUsers.map((user) => (
          <li key={user.id}>
            {user.username}
          </li>
        ))}
      </ul>
      <h2>Filter by Role</h2>
      <select
        value=""
        onChange={(event) => handleFilter(event.target.value)}
      >
        <option value="">Select Role</option>
        {userRoles.map((userRole) => (
          <option key={userRole.roleId} value={userRole.roleId}>
            {userRole.roleName}
          </option>
        ))}
      </select>
    </div>
  );
};

export default UserRolesManagement;
