import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} Cake
 * @property {number} cakeId
 * @property {string} name
 * @property {string} description
 * @property {string} image
 * @property {number} price
 */

/**
 * @typedef {Object} Order
 * @property {number} orderId
 * @property {string} cakeType
 * @property {string} flavor
 * @property {string} design
 * @property {string} message
 * @property {string} pickupOrDelivery
 * @property {string} pickupTime
 * @property {string} deliveryAddress
 * @property {number} quantity
 * @property {number} totalCost
 */

/**
 * @typedef {Object} PickupOption
 * @property {string} option
 * @property {number} cost
 * @property {string} estimatedTime
 */

/**
 * @typedef {Object} DeliveryOption
 * @property {string} option
 * @property {number} cost
 * @property {string} estimatedTime
 */

/**
 * @typedef {Object} RestaurantInfo
 * @property {string} logo
 * @property {Object} contactInfo
 * @property {string} contactInfo.phoneNumber
 * @property {string} contactInfo.email
 * @property {string} contactInfo.address
 */

const HomePage = () => {
  const [cakes, setCakes] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCake, setSelectedCake] = useState(null);
  const [pickupOptions, setPickupOptions] = useState([]);
  const [deliveryOptions, setDeliveryOptions] = useState([]);
  const [order, setOrder] = useState({
    cakeType: '',
    flavor: '',
    design: '',
    message: '',
    pickupOrDelivery: '',
    pickupTime: '',
    deliveryAddress: '',
    quantity: 1,
  });
  const [paymentMethod, setPaymentMethod] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);
  const [restaurantInfo, setRestaurantInfo] = useState({});

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const getCakes = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/cakes');
      setCakes(response.data.cakes);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const searchCakes = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/cakes/search', {
        params: { query: searchQuery },
      });
      setCakes(response.data.cakes);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, searchQuery]);

  const getCakeDetails = useCallback(async (cakeId) => {
    try {
      const response = await axiosInstance.get(`/api/cakes/${cakeId}`);
      setSelectedCake(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getPickupAndDeliveryOptions = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/orders/options');
      setPickupOptions(response.data.pickup_options);
      setDeliveryOptions(response.data.delivery_options);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const createOrder = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/orders', {
        cakeType: order.cakeType,
        flavor: order.flavor,
        design: order.design,
        message: order.message,
        pickupOrDelivery: order.pickupOrDelivery,
        pickupTime: order.pickupTime,
        deliveryAddress: order.deliveryAddress,
        quantity: order.quantity,
      });
      setOrder({
        cakeType: '',
        flavor: '',
        design: '',
        message: '',
        pickupOrDelivery: '',
        pickupTime: '',
        deliveryAddress: '',
        quantity: 1,
      });
      return response.data.orderId;
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, order]);

  const processPayment = useCallback(async (orderId) => {
    try {
      const response = await axiosInstance.post(`/api/orders/${orderId}/payment`, {
        paymentMethod,
        cardNumber,
        expirationDate,
        cvv,
      });
      return response.data.paymentStatus;
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, paymentMethod, cardNumber, expirationDate, cvv]);

  const createAccount = useCallback(async (username, email, password, name) => {
    try {
      const response = await axiosInstance.post('/api/users', {
        username,
        email,
        password,
        name,
      });
      return response.data.userId;
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const login = useCallback(async (username, password) => {
    try {
      const response = await axiosInstance.post('/api/users/login', {
        username,
        password,
      });
      return response.data.userId;
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getOrderHistory = useCallback(async (userId) => {
    try {
      const response = await axiosInstance.get(`/api/users/${userId}/orders`);
      return response.data.orders;
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getRestaurantInfo = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/restaurant/info');
      setRestaurantInfo(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  useEffect(() => {
    getCakes();
    getPickupAndDeliveryOptions();
    getRestaurantInfo();
  }, [getCakes, getPickupAndDeliveryOptions, getRestaurantInfo]);

  const handleSearch = (event) => {
    event.preventDefault();
    searchCakes();
  };

  const handleCakeSelect = (cakeId) => {
    getCakeDetails(cakeId);
  };

  const handleOrderSubmit = (event) => {
    event.preventDefault();
    createOrder().then((orderId) => {
      processPayment(orderId).then((paymentStatus) => {
        if (paymentStatus === 'success') {
          alert('Order placed successfully!');
        } else {
          alert('Payment failed!');
        }
      });
    });
  };

  const handlePaymentMethodChange = (event) => {
    setPaymentMethod(event.target.value);
  };

  const handleCardNumberChange = (event) => {
    setCardNumber(event.target.value);
  };

  const handleExpirationDateChange = (event) => {
    setExpirationDate(event.target.value);
  };

  const handleCvvChange = (event) => {
    setCvv(event.target.value);
  };

  const handleCreateAccount = (event) => {
    event.preventDefault();
    const username = event.target.username.value;
    const email = event.target.email.value;
    const password = event.target.password.value;
    const name = event.target.name.value;
    createAccount(username, email, password, name).then((userId) => {
      setIsLoggedIn(true);
      setUserId(userId);
    });
  };

  const handleLogin = (event) => {
    event.preventDefault();
    const username = event.target.username.value;
    const password = event.target.password.value;
    login(username, password).then((userId) => {
      setIsLoggedIn(true);
      setUserId(userId);
    });
  };

  return (
    <div>
      <header>
        <img src={restaurantInfo.logo} alt="Restaurant Logo" />
        <h1>{restaurantInfo.contactInfo.phoneNumber}</h1>
        <h1>{restaurantInfo.contactInfo.email}</h1>
        <h1>{restaurantInfo.contactInfo.address}</h1>
      </header>
      <main>
        <section>
          <h2>Cakes</h2>
          <ul>
            {cakes.map((cake) => (
              <li key={cake.cakeId}>
                <img src={cake.image} alt={cake.name} />
                <h3>{cake.name}</h3>
                <p>{cake.description}</p>
                <p>Price: ${cake.price}</p>
                <button onClick={() => handleCakeSelect(cake.cakeId)}>Select</button>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Search Cakes</h2>
          <form onSubmit={handleSearch}>
            <input type="search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            <button type="submit">Search</button>
          </form>
        </section>
        {selectedCake && (
          <section>
            <h2>Selected Cake</h2>
            <img src={selectedCake.image} alt={selectedCake.name} />
            <h3>{selectedCake.name}</h3>
            <p>{selectedCake.description}</p>
            <p>Price: ${selectedCake.price}</p>
            <form onSubmit={handleOrderSubmit}>
              <label>
                Flavor:
                <select value={order.flavor} onChange={(event) => setOrder({ ...order, flavor: event.target.value })}>
                  {selectedCake.customizationOptions.map((option) => (
                    <option key={option.optionId} value={option.name}>
                      {option.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Design:
                <select value={order.design} onChange={(event) => setOrder({ ...order, design: event.target.value })}>
                  {selectedCake.customizationOptions.map((option) => (
                    <option key={option.optionId} value={option.name}>
                      {option.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Message:
                <input type="text" value={order.message} onChange={(event) => setOrder({ ...order, message: event.target.value })} />
              </label>
              <label>
                Pickup or Delivery:
                <select value={order.pickupOrDelivery} onChange={(event) => setOrder({ ...order, pickupOrDelivery: event.target.value })}>
                  <option value="pickup">Pickup</option>
                  <option value="delivery">Delivery</option>
                </select>
              </label>
              {order.pickupOrDelivery === 'pickup' && (
                <label>
                  Pickup Time:
                  <input type="datetime-local" value={order.pickupTime} onChange={(event) => setOrder({ ...order, pickupTime: event.target.value })} />
                </label>
              )}
              {order.pickupOrDelivery === 'delivery' && (
                <label>
                  Delivery Address:
                  <input type="text" value={order.deliveryAddress} onChange={(event) => setOrder({ ...order, deliveryAddress: event.target.value })} />
                </label>
              )}
              <label>
                Quantity:
                <input type="number" value={order.quantity} onChange={(event) => setOrder({ ...order, quantity: event.target.valueAsNumber })} />
              </label>
              <button type="submit">Place Order</button>
            </form>
          </section>
        )}
        <section>
          <h2>Payment</h2>
          <form>
            <label>
              Payment Method:
              <select value={paymentMethod} onChange={handlePaymentMethodChange}>
                <option value="credit-card">Credit Card</option>
                <option value="paypal">PayPal</option>
              </select>
            </label>
            {paymentMethod === 'credit-card' && (
              <div>
                <label>
                  Card Number:
                  <input type="text" value={cardNumber} onChange={handleCardNumberChange} />
                </label>
                <label>
                  Expiration Date:
                  <input type="text" value={expirationDate} onChange={handleExpirationDateChange} />
                </label>
                <label>
                  CVV:
                  <input type="text" value={cvv} onChange={handleCvvChange} />
                </label>
              </div>
            )}
          </form>
        </section>
        <section>
          <h2>Account</h2>
          {isLoggedIn ? (
            <div>
              <p>Welcome, {userId}!</p>
              <button onClick={() => setIsLoggedIn(false)}>Logout</button>
              <button onClick={() => getOrderHistory(userId)}>Order History</button>
            </div>
          ) : (
            <div>
              <form onSubmit={handleCreateAccount}>
                <label>
                  Username:
                  <input type="text" name="username" />
                </label>
                <label>
                  Email:
                  <input type="email" name="email" />
                </label>
                <label>
                  Password:
                  <input type="password" name="password" />
                </label>
                <label>
                  Name:
                  <input type="text" name="name" />
                </label>
                <button type="submit">Create Account</button>
              </form>
              <form onSubmit={handleLogin}>
                <label>
                  Username:
                  <input type="text" name="username" />
                </label>
                <label>
                  Password:
                  <input type="password" name="password" />
                </label>
                <button type="submit">Login</button>
              </form>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default HomePage;
