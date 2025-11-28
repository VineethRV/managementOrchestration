import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

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
 * @typedef {Object} Customer
 * @property {number} customer_id
 * @property {string} name
 * @property {string} email
 * @property {string} phone
 */

const OrderHistoryPage = () => {
  const [orders, setOrders] = useState([]);
  const [customer, setCustomer] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ dateRange: '', orderStatus: '' });
  const [search, setSearch] = useState({ date: '', orderStatus: '', cakeType: '' });
  const [pageNumber, setPageNumber] = useState(1);
  const [limit, setLimit] = useState(10);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/api/orders', {
        params: {
          page: pageNumber,
          limit: limit,
        },
      });
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, pageNumber, limit]);

  const fetchCustomer = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/api/customers/me');
      setCustomer(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const handleFilter = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/api/orders/filter', {
        params: {
          date_range: filter.dateRange,
          order_status: filter.orderStatus,
        },
      });
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, filter]);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/api/orders/search', {
        params: {
          date: search.date,
          order_status: search.orderStatus,
          cake_type: search.cakeType,
        },
      });
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, search]);

  useEffect(() => {
    fetchOrders();
    fetchCustomer();
  }, [fetchOrders, fetchCustomer]);

  const handlePageChange = (pageNumber) => {
    setPageNumber(pageNumber);
  };

  const handleLimitChange = (limit) => {
    setLimit(limit);
  };

  const handleFilterChange = (event) => {
    setFilter({ ...filter, [event.target.name]: event.target.value });
  };

  const handleSearchChange = (event) => {
    setSearch({ ...search, [event.target.name]: event.target.value });
  };

  if (loading) {
    return (
      <div>
        <h1>Loading...</h1>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1>Error: {error}</h1>
      </div>
    );
  }

  return (
    <div>
      <h1>Order History Page</h1>
      <h2>
        {customer.name} ({customer.email}) - {customer.phone}
      </h2>
      <button>
        <a href="/">Back to Homepage</a>
      </button>
      <form>
        <label>
          Date Range:
          <input
            type="text"
            name="dateRange"
            value={filter.dateRange}
            onChange={handleFilterChange}
          />
        </label>
        <label>
          Order Status:
          <input
            type="text"
            name="orderStatus"
            value={filter.orderStatus}
            onChange={handleFilterChange}
          />
        </label>
        <button type="button" onClick={handleFilter}>
          Filter
        </button>
      </form>
      <form>
        <label>
          Date:
          <input
            type="text"
            name="date"
            value={search.date}
            onChange={handleSearchChange}
          />
        </label>
        <label>
          Order Status:
          <input
            type="text"
            name="orderStatus"
            value={search.orderStatus}
            onChange={handleSearchChange}
          />
        </label>
        <label>
          Cake Type:
          <input
            type="text"
            name="cakeType"
            value={search.cakeType}
            onChange={handleSearchChange}
          />
        </label>
        <button type="button" onClick={handleSearch}>
          Search
        </button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Order Date</th>
            <th>Order Total</th>
            <th>Order Status</th>
            <th>Cake Details</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.order_id}>
              <td>{order.order_id}</td>
              <td>{order.pickup_time}</td>
              <td>{order.total_cost}</td>
              <td>{order.pickup_or_delivery}</td>
              <td>
                {order.cake_details.cake_type} - {order.cake_details.flavor} -{' '}
                {order.cake_details.design} - {order.cake_details.message}
              </td>
              <td>
                <button>
                  <a href={`/orders/${order.order_id}`}>View Details</a>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={() => handlePageChange(pageNumber - 1)}>Prev</button>
      <button onClick={() => handlePageChange(pageNumber + 1)}>Next</button>
      <select value={limit} onChange={(event) => handleLimitChange(event.target.value)}>
        <option value={10}>10</option>
        <option value={20}>20</option>
        <option value={50}>50</option>
      </select>
    </div>
  );
};

export default OrderHistoryPage;
