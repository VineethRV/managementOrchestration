import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} PickupOption
 * @property {string} id
 * @property {string} address
 * @property {Object[]} time_slots
 * @property {string} time_slots.start_time
 * @property {string} time_slots.end_time
 */

/**
 * @typedef {Object} DeliveryOption
 * @property {string} id
 * @property {string} address
 * @property {Object[]} time_slots
 * @property {string} time_slots.start_time
 * @property {string} time_slots.end_time
 * @property {number} fee
 */

/**
 * @typedef {Object} PaymentMethod
 * @property {string} id
 * @property {string} name
 * @property {string} description
 */

/**
 * @typedef {Object} OrderSummary
 * @property {string} order_id
 * @property {Object} cake_details
 * @property {string} cake_details.name
 * @property {string} cake_details.flavor
 * @property {string} cake_details.design
 * @property {string} cake_details.message
 * @property {Object} pickup_option
 * @property {string} pickup_option.id
 * @property {string} pickup_option.address
 * @property {Object} pickup_option.time_slot
 * @property {string} pickup_option.time_slot.start_time
 * @property {string} pickup_option.time_slot.end_time
 * @property {Object} delivery_option
 * @property {string} delivery_option.id
 * @property {string} delivery_option.address
 * @property {Object} delivery_option.time_slot
 * @property {string} delivery_option.time_slot.start_time
 * @property {string} delivery_option.time_slot.end_time
 * @property {number} delivery_option.fee
 * @property {number} total_cost
 */

/**
 * @typedef {Object} Customer
 * @property {string} name
 * @property {string} email
 * @property {string} password
 * @property {string} phone
 */

const CheckoutPage = () => {
  const [pickupOptions, setPickupOptions] = useState([]);
  const [deliveryOptions, setDeliveryOptions] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [selectedPickupOption, setSelectedPickupOption] = useState(null);
  const [selectedDeliveryOption, setSelectedDeliveryOption] = useState(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [cardNumber, setCardNumber] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [orderSummary, setOrderSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchPickupAndDeliveryOptions = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/checkout/options');
      setPickupOptions(response.data.pickup_options);
      setDeliveryOptions(response.data.delivery_options);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const fetchPaymentMethods = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/checkout/payment-methods');
      setPaymentMethods(response.data.payment_methods);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const handleSelectPickupOption = (option) => {
    setSelectedPickupOption(option);
  };

  const handleSelectDeliveryOption = (option) => {
    setSelectedDeliveryOption(option);
  };

  const handleSelectPaymentMethod = (method) => {
    setSelectedPaymentMethod(method);
  };

  const handlePlaceOrder = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const orderData = {
        cake_id: 'cake-123', // Replace with actual cake ID
        pickup_option_id: selectedPickupOption?.id,
        delivery_option_id: selectedDeliveryOption?.id,
        payment_method_id: selectedPaymentMethod?.id,
        payment_details: {
          card_number: cardNumber,
          expiration_date: expirationDate,
          cvv: cvv,
        },
        customer_name: customerName,
        customer_email: customerEmail,
        customer_phone: customerPhone,
      };
      const response = await axiosInstance.post('/api/checkout/orders', orderData);
      const orderSummaryResponse = await axiosInstance.get('/api/checkout/orders/summary', {
        params: { order_id: response.data.order_id },
      });
      setOrderSummary(orderSummaryResponse.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPickupAndDeliveryOptions();
    fetchPaymentMethods();
  }, [fetchPickupAndDeliveryOptions, fetchPaymentMethods]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Checkout Page</h1>
      <form onSubmit={handlePlaceOrder}>
        <h2>Pickup and Delivery Options</h2>
        <div>
          <h3>Pickup Options</h3>
          <ul>
            {pickupOptions.map((option) => (
              <li key={option.id}>
                <input
                  type="radio"
                  name="pickup-option"
                  value={option.id}
                  checked={selectedPickupOption?.id === option.id}
                  onChange={() => handleSelectPickupOption(option)}
                />
                <span>
                  {option.address} - {option.time_slots[0].start_time} to {option.time_slots[0].end_time}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Delivery Options</h3>
          <ul>
            {deliveryOptions.map((option) => (
              <li key={option.id}>
                <input
                  type="radio"
                  name="delivery-option"
                  value={option.id}
                  checked={selectedDeliveryOption?.id === option.id}
                  onChange={() => handleSelectDeliveryOption(option)}
                />
                <span>
                  {option.address} - {option.time_slots[0].start_time} to {option.time_slots[0].end_time} (Fee: ${option.fee})
                </span>
              </li>
            ))}
          </ul>
        </div>
        <h2>Payment Methods</h2>
        <ul>
          {paymentMethods.map((method) => (
            <li key={method.id}>
              <input
                type="radio"
                name="payment-method"
                value={method.id}
                checked={selectedPaymentMethod?.id === method.id}
                onChange={() => handleSelectPaymentMethod(method)}
              />
              <span>{method.name}</span>
            </li>
          ))}
        </ul>
        <h2>Payment Details</h2>
        <div>
          <label>
            Card Number:
            <input type="text" value={cardNumber} onChange={(event) => setCardNumber(event.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Expiration Date:
            <input type="text" value={expirationDate} onChange={(event) => setExpirationDate(event.target.value)} />
          </label>
        </div>
        <div>
          <label>
            CVV:
            <input type="text" value={cvv} onChange={(event) => setCvv(event.target.value)} />
          </label>
        </div>
        <h2>Customer Information</h2>
        <div>
          <label>
            Name:
            <input type="text" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Email:
            <input type="email" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Phone:
            <input type="text" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
          </label>
        </div>
        <button type="submit">Place Order</button>
      </form>
      {orderSummary && (
        <div>
          <h2>Order Summary</h2>
          <p>Order ID: {orderSummary.order_id}</p>
          <p>Cake Details: {orderSummary.cake_details.name}</p>
          <p>Pickup Option: {orderSummary.pickup_option.address}</p>
          <p>Delivery Option: {orderSummary.delivery_option.address}</p>
          <p>Total Cost: ${orderSummary.total_cost}</p>
        </div>
      )}
    </div>
  );
};

export default CheckoutPage;
