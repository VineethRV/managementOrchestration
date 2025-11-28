import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * Admin Dashboard component
 * @returns {JSX.Element}
 */
function AdminDashboard() {
  // State to store sales metrics
  const [salesMetrics, setSalesMetrics] = useState({
    totalOrders: 0,
    totalRevenue: 0,
    revenueBreakdown: {
      onlineOrders: 0,
      inStoreOrders: 0,
    },
    orderStatus: {
      pending: 0,
      inProgress: 0,
      completed: 0,
    },
  });

  // State to store orders
  const [orders, setOrders] = useState([]);

  // State to store search query
  const [searchQuery, setSearchQuery] = useState('');

  // State to store selected order
  const [selectedOrder, setSelectedOrder] = useState(null);

  // State to store update order status form data
  const [updateOrderStatusFormData, setUpdateOrderStatusFormData] = useState({
    orderStatus: '',
    notes: '',
  });

  // State to store calendar view data
  const [calendarViewData, setCalendarViewData] = useState({
    upcomingOrders: [],
  });

  // State to store low stock alerts
  const [lowStockAlerts, setLowStockAlerts] = useState([]);

  // State to store cake menu items
  const [cakeMenuItems, setCakeMenuItems] = useState([]);

  // State to store customer accounts
  const [customerAccounts, setCustomerAccounts] = useState([]);

  // State to store payment metrics
  const [paymentMetrics, setPaymentMetrics] = useState({
    totalPayments: 0,
    paymentMethods: {
      creditCard: 0,
      paypal: 0,
    },
  });

  // State to store restaurant settings
  const [restaurantSettings, setRestaurantSettings] = useState({
    businessHours: '',
    contactInfo: '',
  });

  // State to store loading and error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to fetch sales metrics
  const fetchSalesMetrics = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/sales-metrics');
      setSalesMetrics(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to fetch orders
  const fetchOrders = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/orders');
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to search orders
  const searchOrders = useCallback(async (query) => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/orders/search', {
        params: {
          customerName: query,
        },
      });
      setOrders(response.data.orders);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to update order status
  const updateOrderStatus = useCallback(async (orderId, orderStatus, notes) => {
    try {
      const response = await axios.put(`http://localhost:5000/api/admin/orders/${orderId}`, {
        orderStatus,
        notes,
      });
      setOrders(
        orders.map((order) =>
          order.orderId === orderId ? { ...order, orderStatus, notes } : order
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }, [orders]);

  // Function to fetch calendar view data
  const fetchCalendarViewData = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/calendar');
      setCalendarViewData(response.data.calendar);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to fetch low stock alerts
  const fetchLowStockAlerts = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/low-stock-alerts');
      setLowStockAlerts(response.data.lowStockAlerts);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to fetch cake menu items
  const fetchCakeMenuItems = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/cake-menu-items');
      setCakeMenuItems(response.data.cakeMenuItems);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to add cake menu item
  const addCakeMenuItem = useCallback(async (cakeName, description, price) => {
    try {
      const response = await axios.post('http://localhost:5000/api/admin/cake-menu-items', {
        cakeName,
        description,
        price,
      });
      setCakeMenuItems([...cakeMenuItems, response.data]);
    } catch (error) {
      setError(error.message);
    }
  }, [cakeMenuItems]);

  // Function to update cake menu item
  const updateCakeMenuItem = useCallback(async (menuItemId, cakeName, description, price) => {
    try {
      const response = await axios.put(`http://localhost:5000/api/admin/cake-menu-items/${menuItemId}`, {
        cakeName,
        description,
        price,
      });
      setCakeMenuItems(
        cakeMenuItems.map((menuItem) =>
          menuItem.menuItemId === menuItemId ? { ...menuItem, cakeName, description, price } : menuItem
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }, [cakeMenuItems]);

  // Function to delete cake menu item
  const deleteCakeMenuItem = useCallback(async (menuItemId) => {
    try {
      await axios.delete(`http://localhost:5000/api/admin/cake-menu-items/${menuItemId}`);
      setCakeMenuItems(cakeMenuItems.filter((menuItem) => menuItem.menuItemId !== menuItemId));
    } catch (error) {
      setError(error.message);
    }
  }, [cakeMenuItems]);

  // Function to fetch customer accounts
  const fetchCustomerAccounts = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/customers');
      setCustomerAccounts(response.data.customers);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to fetch payment metrics
  const fetchPaymentMetrics = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/payment-metrics');
      setPaymentMetrics(response.data.paymentMetrics);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to fetch restaurant settings
  const fetchRestaurantSettings = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/restaurant-settings');
      setRestaurantSettings(response.data.restaurantSettings);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Function to update restaurant settings
  const updateRestaurantSettings = useCallback(async (businessHours, contactInfo) => {
    try {
      const response = await axios.put('http://localhost:5000/api/admin/restaurant-settings', {
        businessHours,
        contactInfo,
      });
      setRestaurantSettings(response.data.restaurantSettings);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  // Use effect to fetch data on mount
  useEffect(() => {
    fetchSalesMetrics();
    fetchOrders();
    fetchCalendarViewData();
    fetchLowStockAlerts();
    fetchCakeMenuItems();
    fetchCustomerAccounts();
    fetchPaymentMetrics();
    fetchRestaurantSettings();
  }, [
    fetchSalesMetrics,
    fetchOrders,
    fetchCalendarViewData,
    fetchLowStockAlerts,
    fetchCakeMenuItems,
    fetchCustomerAccounts,
    fetchPaymentMetrics,
    fetchRestaurantSettings,
  ]);

  // Handle search query change
  const handleSearchQueryChange = (event) => {
    setSearchQuery(event.target.value);
  };

  // Handle update order status form submission
  const handleUpdateOrderStatusFormSubmission = (event) => {
    event.preventDefault();
    updateOrderStatus(selectedOrder.orderId, updateOrderStatusFormData.orderStatus, updateOrderStatusFormData.notes);
  };

  // Handle add cake menu item form submission
  const handleAddCakeMenuItemFormSubmission = (event) => {
    event.preventDefault();
    addCakeMenuItem(event.target.cakeName.value, event.target.description.value, event.target.price.value);
  };

  // Handle update cake menu item form submission
  const handleUpdateCakeMenuItemFormSubmission = (event) => {
    event.preventDefault();
    updateCakeMenuItem(event.target.menuItemId.value, event.target.cakeName.value, event.target.description.value, event.target.price.value);
  };

  // Handle delete cake menu item
  const handleDeleteCakeMenuItem = (menuItemId) => {
    deleteCakeMenuItem(menuItemId);
  };

  // Handle update restaurant settings form submission
  const handleUpdateRestaurantSettingsFormSubmission = (event) => {
    event.preventDefault();
    updateRestaurantSettings(event.target.businessHours.value, event.target.contactInfo.value);
  };

  // Render loading state
  if (loading) {
    return <div>Loading...</div>;
  }

  // Render error state
  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Admin Dashboard</h1>
      <section>
        <h2>Sales Metrics</h2>
        <p>Total Orders: {salesMetrics.totalOrders}</p>
        <p>Total Revenue: {salesMetrics.totalRevenue}</p>
        <p>Revenue Breakdown:</p>
        <ul>
          <li>Online Orders: {salesMetrics.revenueBreakdown.onlineOrders}</li>
          <li>In-Store Orders: {salesMetrics.revenueBreakdown.inStoreOrders}</li>
        </ul>
        <p>Order Status:</p>
        <ul>
          <li>Pending: {salesMetrics.orderStatus.pending}</li>
          <li>In Progress: {salesMetrics.orderStatus.inProgress}</li>
          <li>Completed: {salesMetrics.orderStatus.completed}</li>
        </ul>
      </section>
      <section>
        <h2>Orders</h2>
        <input
          type="search"
          value={searchQuery}
          onChange={handleSearchQueryChange}
          placeholder="Search orders by customer name, order ID, or date"
        />
        <ul>
          {orders.map((order) => (
            <li key={order.orderId}>
              <p>Order ID: {order.orderId}</p>
              <p>Customer Name: {order.customerName}</p>
              <p>Order Date: {order.orderDate}</p>
              <p>Order Status: {order.orderStatus}</p>
              <button onClick={() => setSelectedOrder(order)}>Update Order Status</button>
            </li>
          ))}
        </ul>
        {selectedOrder && (
          <form onSubmit={handleUpdateOrderStatusFormSubmission}>
            <label>
              Order Status:
              <select
                value={updateOrderStatusFormData.orderStatus}
                onChange={(event) =>
                  setUpdateOrderStatusFormData({ ...updateOrderStatusFormData, orderStatus: event.target.value })
                }
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </label>
            <label>
              Notes:
              <textarea
                value={updateOrderStatusFormData.notes}
                onChange={(event) =>
                  setUpdateOrderStatusFormData({ ...updateOrderStatusFormData, notes: event.target.value })
                }
              />
            </label>
            <button type="submit">Update Order Status</button>
          </form>
        )}
      </section>
      <section>
        <h2>Calendar View</h2>
        <ul>
          {calendarViewData.upcomingOrders.map((order) => (
            <li key={order.orderId}>
              <p>Order ID: {order.orderId}</p>
              <p>Order Date: {order.orderDate}</p>
              <p>Pickup Time: {order.pickupTime}</p>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Low Stock Alerts</h2>
        <ul>
          {lowStockAlerts.map((alert) => (
            <li key={alert.ingredient}>
              <p>Ingredient: {alert.ingredient}</p>
              <p>Quantity: {alert.quantity}</p>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Cake Menu Items</h2>
        <ul>
          {cakeMenuItems.map((menuItem) => (
            <li key={menuItem.menuItemId}>
              <p>Cake Name: {menuItem.cakeName}</p>
              <p>Description: {menuItem.description}</p>
              <p>Price: {menuItem.price}</p>
              <button onClick={() => handleDeleteCakeMenuItem(menuItem.menuItemId)}>Delete</button>
            </li>
          ))}
        </ul>
        <form onSubmit={handleAddCakeMenuItemFormSubmission}>
          <label>
            Cake Name:
            <input type="text" name="cakeName" />
          </label>
          <label>
            Description:
            <input type="text" name="description" />
          </label>
          <label>
            Price:
            <input type="number" name="price" />
          </label>
          <button type="submit">Add Cake Menu Item</button>
        </form>
      </section>
      <section>
        <h2>Customer Accounts</h2>
        <ul>
          {customerAccounts.map((customer) => (
            <li key={customer.customerId}>
              <p>Customer Name: {customer.customerName}</p>
              <p>Order History:</p>
              <ul>
                {customer.orderHistory.map((order) => (
                  <li key={order.orderId}>
                    <p>Order ID: {order.orderId}</p>
                    <p>Order Date: {order.orderDate}</p>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Payment Metrics</h2>
        <p>Total Payments: {paymentMetrics.totalPayments}</p>
        <p>Payment Methods:</p>
        <ul>
          <li>Credit Card: {paymentMetrics.paymentMethods.creditCard}</li>
          <li>PayPal: {paymentMetrics.paymentMethods.paypal}</li>
        </ul>
      </section>
      <section>
        <h2>Restaurant Settings</h2>
        <form onSubmit={handleUpdateRestaurantSettingsFormSubmission}>
          <label>
            Business Hours:
            <input type="text" name="businessHours" value={restaurantSettings.businessHours} />
          </label>
          <label>
            Contact Info:
            <input type="text" name="contactInfo" value={restaurantSettings.contactInfo} />
          </label>
          <button type="submit">Update Restaurant Settings</button>
        </form>
      </section>
    </div>
  );
}

export default AdminDashboard;
