import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} AccountInfo
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {string} phone
 * @property {string} address
 */

/**
 * @typedef {Object} Order
 * @property {number} order_id
 * @property {Object} cake_details
 * @property {string} cake_details.cake_type
 * @property {string} cake_details.flavor
 * @property {string} cake_details.design
 * @property {string} cake_details.message
 * @property {string} pickup_or_delivery
 * @property {string} pickup_time
 * @property {string} delivery_address
 * @property {number} quantity
 * @property {number} total_cost
 */

/**
 * @typedef {Object} LoyaltyPoints
 * @property {number} loyalty_points
 * @property {string} reward_tier
 */

const AccountDashboard = () => {
  const [accountInfo, setAccountInfo] = useState(null);
  const [orders, setOrders] = useState([]);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loyaltyPoints, setLoyaltyPoints] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedAccountInfo, setEditedAccountInfo] = useState({});

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const fetchAccountInfo = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/account');
      setAccountInfo(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchOrders = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/orders');
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchRecentOrders = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/orders/recent');
      setRecentOrders(response.data.recent_orders);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchLoyaltyPoints = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/account/loyalty');
      setLoyaltyPoints(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleSearch = useCallback(async (query) => {
    try {
      const response = await axiosInstance.get('/api/orders/search', {
        params: {
          date: query.date,
          order_status: query.order_status,
          cake_type: query.cake_type,
        },
      });
      setSearchResults(response.data.orders);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleEditAccountInfo = useCallback((info) => {
    setEditedAccountInfo(info);
    setIsEditing(true);
  }, []);

  const handleUpdateAccountInfo = useCallback(async (info) => {
    try {
      const response = await axiosInstance.put('/api/account', info);
      setAccountInfo(response.data);
      setIsEditing(false);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleLogout = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/logout');
      // Handle logout logic
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    fetchAccountInfo();
    fetchOrders();
    fetchRecentOrders();
    fetchLoyaltyPoints();
  }, [fetchAccountInfo, fetchOrders, fetchRecentOrders, fetchLoyaltyPoints]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Account Dashboard</h1>
      {accountInfo && (
        <div>
          <h2>Account Information</h2>
          <p>Name: {accountInfo.name}</p>
          <p>Email: {accountInfo.email}</p>
          <p>Phone: {accountInfo.phone}</p>
          <p>Address: {accountInfo.address}</p>
          {isEditing ? (
            <form onSubmit={(e) => {
              e.preventDefault();
              handleUpdateAccountInfo(editedAccountInfo);
            }}>
              <label>
                Name:
                <input type="text" value={editedAccountInfo.name} onChange={(e) => setEditedAccountInfo({ ...editedAccountInfo, name: e.target.value })} />
              </label>
              <label>
                Email:
                <input type="email" value={editedAccountInfo.email} onChange={(e) => setEditedAccountInfo({ ...editedAccountInfo, email: e.target.value })} />
              </label>
              <label>
                Phone:
                <input type="text" value={editedAccountInfo.phone} onChange={(e) => setEditedAccountInfo({ ...editedAccountInfo, phone: e.target.value })} />
              </label>
              <label>
                Address:
                <input type="text" value={editedAccountInfo.address} onChange={(e) => setEditedAccountInfo({ ...editedAccountInfo, address: e.target.value })} />
              </label>
              <button type="submit">Update</button>
            </form>
          ) : (
            <button onClick={() => handleEditAccountInfo(accountInfo)}>Edit</button>
          )}
        </div>
      )}
      <h2>Order History</h2>
      <ul>
        {orders.map((order) => (
          <li key={order.order_id}>
            <p>Cake Type: {order.cake_details.cake_type}</p>
            <p>Flavor: {order.cake_details.flavor}</p>
            <p>Design: {order.cake_details.design}</p>
            <p>Message: {order.cake_details.message}</p>
            <p>Pickup/Delivery: {order.pickup_or_delivery}</p>
            <p>Pickup Time: {order.pickup_time}</p>
            <p>Delivery Address: {order.delivery_address}</p>
            <p>Quantity: {order.quantity}</p>
            <p>Total Cost: {order.total_cost}</p>
            <button onClick={() => handleSearch({ date: '', order_status: '', cake_type: order.cake_details.cake_type })}>View Details</button>
          </li>
        ))}
      </ul>
      <h2>Recent Orders</h2>
      <ul>
        {recentOrders.map((order) => (
          <li key={order.order_id}>
            <p>Cake Type: {order.cake_details.cake_type}</p>
            <p>Flavor: {order.cake_details.flavor}</p>
            <p>Design: {order.cake_details.design}</p>
            <p>Message: {order.cake_details.message}</p>
            <p>Pickup/Delivery: {order.pickup_or_delivery}</p>
            <p>Pickup Time: {order.pickup_time}</p>
            <p>Delivery Address: {order.delivery_address}</p>
            <p>Quantity: {order.quantity}</p>
            <p>Total Cost: {order.total_cost}</p>
          </li>
        ))}
      </ul>
      {loyaltyPoints && (
        <div>
          <h2>Loyalty Points</h2>
          <p>Loyalty Points: {loyaltyPoints.loyalty_points}</p>
          <p>Reward Tier: {loyaltyPoints.reward_tier}</p>
        </div>
      )}
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
};

export default AccountDashboard;
