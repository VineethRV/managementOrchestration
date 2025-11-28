import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} OrderDetails
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
 * @typedef {Object} OrderPaymentDetails
 * @property {number} order_total
 * @property {string} payment_method
 * @property {string} payment_status
 */

/**
 * @typedef {Object} OrderConfirmationNumber
 * @property {string} confirmation_number
 */

/**
 * @typedef {Object} RestaurantContactInfo
 * @property {string} phone_number
 * @property {string} email
 */

/**
 * @typedef {Object} RestaurantSocialMediaLinks
 * @property {string} facebook
 * @property {string} instagram
 * @property {string} twitter
 */

const OrderConfirmationPage = ({ orderId }) => {
  const [orderDetails, setOrderDetails] = useState({});
  const [pickupDeliveryDetails, setPickupDeliveryDetails] = useState({});
  const [orderPaymentDetails, setOrderPaymentDetails] = useState({});
  const [orderConfirmationNumber, setOrderConfirmationNumber] = useState('');
  const [restaurantContactInfo, setRestaurantContactInfo] = useState({});
  const [restaurantSocialMediaLinks, setRestaurantSocialMediaLinks] = useState({});
  const [receipt, setReceipt] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const fetchOrderDetails = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders/${orderId}`);
      setOrderDetails(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [orderId]);

  const fetchPickupDeliveryDetails = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders/${orderId}/pickup-delivery`);
      setPickupDeliveryDetails(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [orderId]);

  const fetchOrderPaymentDetails = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders/${orderId}/payment`);
      setOrderPaymentDetails(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [orderId]);

  const fetchOrderConfirmationNumber = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders/${orderId}/confirmation-number`);
      setOrderConfirmationNumber(response.data.confirmation_number);
    } catch (error) {
      setError(error.message);
    }
  }, [orderId]);

  const fetchRestaurantContactInfo = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/restaurant/contact-info');
      setRestaurantContactInfo(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const fetchRestaurantSocialMediaLinks = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/restaurant/social-media-links');
      setRestaurantSocialMediaLinks(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const fetchReceipt = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders/${orderId}/receipt`);
      setReceipt(response.data.receipt);
    } catch (error) {
      setError(error.message);
    }
  }, [orderId]);

  const handleViewOrderHistory = () => {
    // Implement logic to view order history
  };

  useEffect(() => {
    const fetchAllData = async () => {
      await Promise.all([
        fetchOrderDetails(),
        fetchPickupDeliveryDetails(),
        fetchOrderPaymentDetails(),
        fetchOrderConfirmationNumber(),
        fetchRestaurantContactInfo(),
        fetchRestaurantSocialMediaLinks(),
        fetchReceipt(),
      ]);
      setLoading(false);
    };
    fetchAllData();
  }, [
    fetchOrderDetails,
    fetchPickupDeliveryDetails,
    fetchOrderPaymentDetails,
    fetchOrderConfirmationNumber,
    fetchRestaurantContactInfo,
    fetchRestaurantSocialMediaLinks,
    fetchReceipt,
  ]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Order Confirmation</h1>
      <p>Order Confirmation Number: {orderConfirmationNumber}</p>
      <h2>Order Summary</h2>
      <ul>
        <li>Cake Type: {orderDetails.cake_details?.cake_type}</li>
        <li>Flavor: {orderDetails.cake_details?.flavor}</li>
        <li>Design: {orderDetails.cake_details?.design}</li>
        <li>Message: {orderDetails.cake_details?.message}</li>
        <li>Quantity: {orderDetails.quantity}</li>
      </ul>
      <h2>Pickup/Delivery Details</h2>
      <ul>
        <li>Pickup Time: {pickupDeliveryDetails.pickup_time}</li>
        <li>Delivery Address: {pickupDeliveryDetails.delivery_address}</li>
      </ul>
      <h2>Payment Details</h2>
      <ul>
        <li>Order Total: {orderPaymentDetails.order_total}</li>
        <li>Payment Method: {orderPaymentDetails.payment_method}</li>
        <li>Payment Status: {orderPaymentDetails.payment_status}</li>
      </ul>
      {isLoggedIn && (
        <button onClick={handleViewOrderHistory}>View Order History</button>
      )}
      <button onClick={() => window.print()}>Print Receipt</button>
      <button onClick={() => window.open(`data:application/pdf;base64,${receipt}`, '_blank')}>Download Receipt</button>
      <p>Thank you for your order! Your order will be ready for pickup on {pickupDeliveryDetails.pickup_time} at our restaurant located at {pickupDeliveryDetails.delivery_address}. If you have any questions or concerns, please don't hesitate to contact us.</p>
      <p>Follow us on social media:</p>
      <ul>
        <li>
          <a href={restaurantSocialMediaLinks.facebook} target="_blank" rel="noreferrer">
            Facebook
          </a>
        </li>
        <li>
          <a href={restaurantSocialMediaLinks.instagram} target="_blank" rel="noreferrer">
            Instagram
          </a>
        </li>
        <li>
          <a href={restaurantSocialMediaLinks.twitter} target="_blank" rel="noreferrer">
            Twitter
          </a>
        </li>
      </ul>
      <p>Contact us:</p>
      <ul>
        <li>Phone: {restaurantContactInfo.phone_number}</li>
        <li>Email: {restaurantContactInfo.email}</li>
      </ul>
    </div>
  );
};

export default OrderConfirmationPage;
