import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} CartItem
 * @property {number} itemId
 * @property {number} cakeId
 * @property {number} quantity
 * @property {Object} customizations
 * @property {string} customizations.flavor
 * @property {string} customizations.design
 * @property {string} customizations.message
 * @property {number} price
 */

/**
 * @typedef {Object} PickupDeliveryOption
 * @property {number} optionId
 * @property {string} description
 * @property {number} cost
 * @property {string} timeFrame
 */

/**
 * @typedef {Object} OrderSummary
 * @property {CartItem[]} cartItems
 * @property {PickupDeliveryOption} pickupDeliveryOption
 * @property {string} paymentMethod
 */

/**
 * @typedef {Object} PaymentDetails
 * @property {string} cardNumber
 * @property {string} expirationDate
 * @property {string} cvv
 */

const CartPage = () => {
  const [cartItems, setCartItems] = useState([]);
  const [pickupDeliveryOptions, setPickupDeliveryOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [promoCode, setPromoCode] = useState('');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [newTotal, setNewTotal] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [paymentDetails, setPaymentDetails] = useState({});
  const [validationStatus, setValidationStatus] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const fetchCartItems = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/cart/items');
      setCartItems(response.data.cartItems);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchPickupDeliveryOptions = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/cart/pickup-delivery-options');
      setPickupDeliveryOptions(response.data.pickupOptions.concat(response.data.deliveryOptions));
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateQuantity = useCallback(async (itemId, quantity) => {
    try {
      const response = await axiosInstance.put(`/api/cart/items/${itemId}/quantity`, { quantity });
      setCartItems(cartItems.map(item => item.itemId === itemId ? { ...item, quantity: response.data.quantity } : item));
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, cartItems]);

  const removeItem = useCallback(async (itemId) => {
    try {
      await axiosInstance.delete(`/api/cart/items/${itemId}`);
      setCartItems(cartItems.filter(item => item.itemId !== itemId));
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, cartItems]);

  const applyPromoCode = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/cart/promo-code', { promoCode });
      setDiscountAmount(response.data.discountAmount);
      setNewTotal(response.data.newTotal);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, promoCode]);

  const proceedToCheckout = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/cart/checkout');
      // Handle checkout response
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const processPayment = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/cart/payment', { paymentMethod, paymentDetails });
      setValidationStatus(response.data.paymentStatus);
      // Handle payment response
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, paymentMethod, paymentDetails]);

  const validatePayment = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/cart/payment/validate', { paymentMethod, paymentDetails });
      setValidationStatus(response.data.validationStatus);
      setErrors(response.data.errors);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, paymentMethod, paymentDetails]);

  useEffect(() => {
    fetchCartItems();
    fetchPickupDeliveryOptions();
  }, [fetchCartItems, fetchPickupDeliveryOptions]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Cart Page</h1>
      <ul>
        {cartItems.map(item => (
          <li key={item.itemId}>
            <span>{item.cakeId}</span>
            <span>Quantity: {item.quantity}</span>
            <span>Flavor: {item.customizations.flavor}</span>
            <span>Design: {item.customizations.design}</span>
            <span>Message: {item.customizations.message}</span>
            <span>Price: {item.price}</span>
            <button onClick={() => updateQuantity(item.itemId, item.quantity + 1)}>+</button>
            <button onClick={() => updateQuantity(item.itemId, item.quantity - 1)}>-</button>
            <button onClick={() => removeItem(item.itemId)}>Remove</button>
          </li>
        ))}
      </ul>
      <div>
        <h2>Pickup and Delivery Options</h2>
        <ul>
          {pickupDeliveryOptions.map(option => (
            <li key={option.optionId}>
              <span>{option.description}</span>
              <span>Cost: {option.cost}</span>
              <span>Time Frame: {option.timeFrame}</span>
              <button onClick={() => setSelectedOption(option)}>Select</button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Promo Code</h2>
        <input type="text" value={promoCode} onChange={e => setPromoCode(e.target.value)} />
        <button onClick={applyPromoCode}>Apply</button>
        <span>Discount Amount: {discountAmount}</span>
        <span>New Total: {newTotal}</span>
      </div>
      <div>
        <h2>Payment Method</h2>
        <select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)}>
          <option value="">Select Payment Method</option>
          <option value="credit-card">Credit Card</option>
          <option value="paypal">PayPal</option>
        </select>
        {paymentMethod === 'credit-card' && (
          <div>
            <input type="text" placeholder="Card Number" value={paymentDetails.cardNumber} onChange={e => setPaymentDetails({ ...paymentDetails, cardNumber: e.target.value })} />
            <input type="text" placeholder="Expiration Date" value={paymentDetails.expirationDate} onChange={e => setPaymentDetails({ ...paymentDetails, expirationDate: e.target.value })} />
            <input type="text" placeholder="CVV" value={paymentDetails.cvv} onChange={e => setPaymentDetails({ ...paymentDetails, cvv: e.target.value })} />
          </div>
        )}
        <button onClick={validatePayment}>Validate Payment</button>
        <span>Validation Status: {validationStatus}</span>
        {Object.keys(errors).map(field => (
          <span key={field}>{field}: {errors[field]}</span>
        ))}
      </div>
      <button onClick={proceedToCheckout}>Proceed to Checkout</button>
      <button onClick={processPayment}>Process Payment</button>
    </div>
  );
};

export default CartPage;
