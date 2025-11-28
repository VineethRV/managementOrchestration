import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} PaymentMethod
 * @property {number} id
 * @property {string} name
 * @property {string} description
 */

/**
 * @typedef {Object} OrderSummary
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
 * @typedef {Object} PaymentResponse
 * @property {string} payment_id
 * @property {string} status
 * @property {string} message
 */

/**
 * @typedef {Object} PaymentInfo
 * @property {string} cardNumber
 * @property {string} expirationDate
 * @property {string} cvv
 * @property {string} billingAddress
 */

/**
 * PaymentPage component
 * @returns {JSX.Element}
 */
function PaymentPage() {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [orderSummary, setOrderSummary] = useState({});
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [cardNumber, setCardNumber] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [billingAddress, setBillingAddress] = useState('');
  const [savePaymentInfo, setSavePaymentInfo] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [createAccountUsername, setCreateAccountUsername] = useState('');
  const [createAccountEmail, setCreateAccountEmail] = useState('');
  const [createAccountPassword, setCreateAccountPassword] = useState('');
  const [createAccountConfirmPassword, setCreateAccountConfirmPassword] = useState('');
  const [paymentResponse, setPaymentResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const getPaymentMethods = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/payment-methods');
      setPaymentMethods(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getOrderSummary = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/orders/summary');
      setOrderSummary(response.data.order_summary);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const processPayment = useCallback(async () => {
    try {
      setLoading(true);
      const paymentData = {
        payment_method: selectedPaymentMethod.name,
        card_number: cardNumber,
        expiration_date: expirationDate,
        cvv: cvv,
        amount: orderSummary.total_cost,
        order_id: '12345', // Replace with actual order ID
      };
      const response = await axiosInstance.post('/api/payments', paymentData);
      setPaymentResponse(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, selectedPaymentMethod, cardNumber, expirationDate, cvv, orderSummary, setSelectedPaymentMethod]);

  const savePaymentInformation = useCallback(async () => {
    try {
      const paymentInfo = {
        cardNumber: cardNumber,
        expirationDate: expirationDate,
        cvv: cvv,
        billingAddress: billingAddress,
      };
      const response = await axiosInstance.post('/api/users/payment-info', paymentInfo);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, cardNumber, expirationDate, cvv, billingAddress]);

  const login = useCallback(async () => {
    try {
      const loginData = {
        username: loginUsername,
        password: loginPassword,
      };
      const response = await axiosInstance.post('/api/auth/login', loginData);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, loginUsername, loginPassword]);

  const createAccount = useCallback(async () => {
    try {
      const createAccountData = {
        username: createAccountUsername,
        email: createAccountEmail,
        password: createAccountPassword,
        confirm_password: createAccountConfirmPassword,
      };
      const response = await axiosInstance.post('/api/auth/register', createAccountData);
      console.log(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, createAccountUsername, createAccountEmail, createAccountPassword, createAccountConfirmPassword]);

  useEffect(() => {
    getPaymentMethods();
    getOrderSummary();
  }, [getPaymentMethods, getOrderSummary]);

  const handlePaymentMethodChange = (event) => {
    const selectedMethod = paymentMethods.find((method) => method.name === event.target.value);
    setSelectedPaymentMethod(selectedMethod);
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

  const handleBillingAddressChange = (event) => {
    setBillingAddress(event.target.value);
  };

  const handleSavePaymentInfoChange = (event) => {
    setSavePaymentInfo(event.target.checked);
  };

  const handleLoginUsernameChange = (event) => {
    setLoginUsername(event.target.value);
  };

  const handleLoginPasswordChange = (event) => {
    setLoginPassword(event.target.value);
  };

  const handleCreateAccountUsernameChange = (event) => {
    setCreateAccountUsername(event.target.value);
  };

  const handleCreateAccountEmailChange = (event) => {
    setCreateAccountEmail(event.target.value);
  };

  const handleCreateAccountPasswordChange = (event) => {
    setCreateAccountPassword(event.target.value);
  };

  const handleCreateAccountConfirmPasswordChange = (event) => {
    setCreateAccountConfirmPassword(event.target.value);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Payment Page</h1>
      <h2>Order Summary</h2>
      <p>Cake Type: {orderSummary.cake_details?.cake_type}</p>
      <p>Flavor: {orderSummary.cake_details?.flavor}</p>
      <p>Design: {orderSummary.cake_details?.design}</p>
      <p>Message: {orderSummary.cake_details?.message}</p>
      <p>Pickup/Delivery: {orderSummary.pickup_or_delivery}</p>
      <p>Pickup Time: {orderSummary.pickup_time}</p>
      <p>Delivery Address: {orderSummary.delivery_address}</p>
      <p>Quantity: {orderSummary.quantity}</p>
      <p>Total Cost: {orderSummary.total_cost}</p>
      <h2>Payment Methods</h2>
      <select value={selectedPaymentMethod?.name} onChange={handlePaymentMethodChange}>
        <option value="">Select Payment Method</option>
        {paymentMethods.map((method) => (
          <option key={method.id} value={method.name}>
            {method.name}
          </option>
        ))}
      </select>
      {selectedPaymentMethod?.name === 'Credit Card' && (
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
          <label>
            Billing Address:
            <input type="text" value={billingAddress} onChange={handleBillingAddressChange} />
          </label>
        </div>
      )}
      <label>
        Save Payment Information:
        <input type="checkbox" checked={savePaymentInfo} onChange={handleSavePaymentInfoChange} />
      </label>
      <button onClick={processPayment}>Pay Now</button>
      {paymentResponse && (
        <div>
          <p>Payment ID: {paymentResponse.payment_id}</p>
          <p>Status: {paymentResponse.status}</p>
          <p>Message: {paymentResponse.message}</p>
        </div>
      )}
      <h2>Login</h2>
      <label>
        Username:
        <input type="text" value={loginUsername} onChange={handleLoginUsernameChange} />
      </label>
      <label>
        Password:
        <input type="password" value={loginPassword} onChange={handleLoginPasswordChange} />
      </label>
      <button onClick={login}>Login</button>
      <h2>Create Account</h2>
      <label>
        Username:
        <input type="text" value={createAccountUsername} onChange={handleCreateAccountUsernameChange} />
      </label>
      <label>
        Email:
        <input type="email" value={createAccountEmail} onChange={handleCreateAccountEmailChange} />
      </label>
      <label>
        Password:
        <input type="password" value={createAccountPassword} onChange={handleCreateAccountPasswordChange} />
      </label>
      <label>
        Confirm Password:
        <input type="password" value={createAccountConfirmPassword} onChange={handleCreateAccountConfirmPasswordChange} />
      </label>
      <button onClick={createAccount}>Create Account</button>
    </div>
  );
}

export default PaymentPage;
