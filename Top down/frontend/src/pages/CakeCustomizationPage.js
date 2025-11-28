import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * CakeCustomizationPage component
 * 
 * @returns {JSX.Element} Cake customization page component
 */
function CakeCustomizationPage() {
  // State to store cake options
  const [cakeOptions, setCakeOptions] = useState([]);
  // State to store selected cake option
  const [selectedCakeOption, setSelectedCakeOption] = useState(null);
  // State to store cake flavors
  const [cakeFlavors, setCakeFlavors] = useState([]);
  // State to store selected cake flavor
  const [selectedCakeFlavor, setSelectedCakeFlavor] = useState(null);
  // State to store cake designs
  const [cakeDesigns, setCakeDesigns] = useState([]);
  // State to store selected cake design
  const [selectedCakeDesign, setSelectedCakeDesign] = useState(null);
  // State to store custom message
  const [customMessage, setCustomMessage] = useState('');
  // State to store pickup or delivery option
  const [pickupOrDelivery, setPickupOrDelivery] = useState('pickup');
  // State to store pickup time
  const [pickupTime, setPickupTime] = useState('');
  // State to store delivery address
  const [deliveryAddress, setDeliveryAddress] = useState({
    street: '',
    city: '',
    state: '',
    zip: '',
  });
  // State to store total cost
  const [totalCost, setTotalCost] = useState(0);
  // State to store loading state
  const [isLoading, setIsLoading] = useState(false);
  // State to store error message
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch cake options on component mount
  useEffect(() => {
    const fetchCakeOptions = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/cake-options');
        setCakeOptions(response.data);
      } catch (error) {
        setErrorMessage(error.message);
      }
    };
    fetchCakeOptions();
  }, []);

  // Fetch cake flavors on component mount
  useEffect(() => {
    const fetchCakeFlavors = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/cake-flavors');
        setCakeFlavors(response.data);
      } catch (error) {
        setErrorMessage(error.message);
      }
    };
    fetchCakeFlavors();
  }, []);

  // Fetch cake designs on component mount
  useEffect(() => {
    const fetchCakeDesigns = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/cake-designs');
        setCakeDesigns(response.data);
      } catch (error) {
        setErrorMessage(error.message);
      }
    };
    fetchCakeDesigns();
  }, []);

  // Calculate total cost on change of cake option, flavor, design, or custom message
  useEffect(() => {
    const calculateTotalCost = async () => {
      if (selectedCakeOption && selectedCakeFlavor && selectedCakeDesign) {
        try {
          const response = await axios.post('http://localhost:5000/api/calculate-total-cost', {
            cake_type: selectedCakeOption.name,
            flavor: selectedCakeFlavor.name,
            design: selectedCakeDesign.name,
            message: customMessage,
            pickup_or_delivery: pickupOrDelivery,
            delivery_address: deliveryAddress,
          });
          setTotalCost(response.data.total_cost);
        } catch (error) {
          setErrorMessage(error.message);
        }
      }
    };
    calculateTotalCost();
  }, [selectedCakeOption, selectedCakeFlavor, selectedCakeDesign, customMessage, pickupOrDelivery, deliveryAddress]);

  // Handle change of cake option
  const handleCakeOptionChange = (option) => {
    setSelectedCakeOption(option);
  };

  // Handle change of cake flavor
  const handleCakeFlavorChange = (flavor) => {
    setSelectedCakeFlavor(flavor);
  };

  // Handle change of cake design
  const handleCakeDesignChange = (design) => {
    setSelectedCakeDesign(design);
  };

  // Handle change of custom message
  const handleCustomMessageChange = (event) => {
    setCustomMessage(event.target.value);
  };

  // Handle change of pickup or delivery option
  const handlePickupOrDeliveryChange = (option) => {
    setPickupOrDelivery(option);
  };

  // Handle change of pickup time
  const handlePickupTimeChange = (event) => {
    setPickupTime(event.target.value);
  };

  // Handle change of delivery address
  const handleDeliveryAddressChange = (event) => {
    setDeliveryAddress({
      ...deliveryAddress,
      [event.target.name]: event.target.value,
    });
  };

  // Handle add to cart
  const handleAddToCart = async () => {
    try {
      const response = await axios.post('http://localhost:5000/api/add-to-cart', {
        cake_id: selectedCakeOption.id,
        flavor_id: selectedCakeFlavor.id,
        design_id: selectedCakeDesign.id,
        message: customMessage,
        pickup_or_delivery: pickupOrDelivery,
        quantity: 1,
      });
      console.log(response.data);
    } catch (error) {
      setErrorMessage(error.message);
    }
  };

  // Handle proceed to payment
  const handleProceedToPayment = async () => {
    try {
      const response = await axios.post('http://localhost:5000/api/proceed-to-payment', {
        cake_id: selectedCakeOption.id,
        customizations: {
          flavor: selectedCakeFlavor.name,
          design: selectedCakeDesign.name,
          message: customMessage,
        },
        pickup_or_delivery: pickupOrDelivery,
        address: deliveryAddress,
        payment_method: 'credit card',
      });
      console.log(response.data);
    } catch (error) {
      setErrorMessage(error.message);
    }
  };

  // Render cake options
  const renderCakeOptions = () => {
    if (isLoading) {
      return <p>Loading...</p>;
    }
    if (errorMessage) {
      return <p>{errorMessage}</p>;
    }
    return (
      <select value={selectedCakeOption ? selectedCakeOption.id : ''} onChange={(event) => handleCakeOptionChange(cakeOptions.find((option) => option.id === parseInt(event.target.value)))}>
        <option value="">Select a cake option</option>
        {cakeOptions.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    );
  };

  // Render cake flavors
  const renderCakeFlavors = () => {
    if (isLoading) {
      return <p>Loading...</p>;
    }
    if (errorMessage) {
      return <p>{errorMessage}</p>;
    }
    return (
      <select value={selectedCakeFlavor ? selectedCakeFlavor.id : ''} onChange={(event) => handleCakeFlavorChange(cakeFlavors.find((flavor) => flavor.id === parseInt(event.target.value)))}>
        <option value="">Select a cake flavor</option>
        {cakeFlavors.map((flavor) => (
          <option key={flavor.id} value={flavor.id}>
            {flavor.name}
          </option>
        ))}
      </select>
    );
  };

  // Render cake designs
  const renderCakeDesigns = () => {
    if (isLoading) {
      return <p>Loading...</p>;
    }
    if (errorMessage) {
      return <p>{errorMessage}</p>;
    }
    return (
      <select value={selectedCakeDesign ? selectedCakeDesign.id : ''} onChange={(event) => handleCakeDesignChange(cakeDesigns.find((design) => design.id === parseInt(event.target.value)))}>
        <option value="">Select a cake design</option>
        {cakeDesigns.map((design) => (
          <option key={design.id} value={design.id}>
            {design.name}
          </option>
        ))}
      </select>
    );
  };

  // Render custom message input
  const renderCustomMessageInput = () => {
    return (
      <input type="text" value={customMessage} onChange={handleCustomMessageChange} placeholder="Enter a custom message" />
    );
  };

  // Render pickup or delivery option
  const renderPickupOrDeliveryOption = () => {
    return (
      <select value={pickupOrDelivery} onChange={(event) => handlePickupOrDeliveryChange(event.target.value)}>
        <option value="pickup">Pickup</option>
        <option value="delivery">Delivery</option>
      </select>
    );
  };

  // Render pickup time input
  const renderPickupTimeInput = () => {
    if (pickupOrDelivery === 'pickup') {
      return (
        <input type="datetime-local" value={pickupTime} onChange={handlePickupTimeChange} />
      );
    }
    return null;
  };

  // Render delivery address input
  const renderDeliveryAddressInput = () => {
    if (pickupOrDelivery === 'delivery') {
      return (
        <div>
          <input type="text" name="street" value={deliveryAddress.street} onChange={handleDeliveryAddressChange} placeholder="Street" />
          <input type="text" name="city" value={deliveryAddress.city} onChange={handleDeliveryAddressChange} placeholder="City" />
          <input type="text" name="state" value={deliveryAddress.state} onChange={handleDeliveryAddressChange} placeholder="State" />
          <input type="text" name="zip" value={deliveryAddress.zip} onChange={handleDeliveryAddressChange} placeholder="Zip" />
        </div>
      );
    }
    return null;
  };

  // Render total cost
  const renderTotalCost = () => {
    return (
      <p>Total Cost: ${totalCost}</p>
    );
  };

  // Render add to cart button
  const renderAddToCartButton = () => {
    return (
      <button onClick={handleAddToCart}>Add to Cart</button>
    );
  };

  // Render proceed to payment button
  const renderProceedToPaymentButton = () => {
    return (
      <button onClick={handleProceedToPayment}>Proceed to Payment</button>
    );
  };

  return (
    <div>
      <h1>Cake Customization Page</h1>
      {renderCakeOptions()}
      {renderCakeFlavors()}
      {renderCakeDesigns()}
      {renderCustomMessageInput()}
      {renderPickupOrDeliveryOption()}
      {renderPickupTimeInput()}
      {renderDeliveryAddressInput()}
      {renderTotalCost()}
      {renderAddToCartButton()}
      {renderProceedToPaymentButton()}
    </div>
  );
}

export default CakeCustomizationPage;
