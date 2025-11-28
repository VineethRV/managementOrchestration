import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} Cake
 * @property {number} cakeId
 * @property {string} name
 * @property {string} description
 * @property {string} image
 * @property {number} price
 * @property {number} quantity
 */

/**
 * @typedef {Object} CakeOption
 * @property {number} optionId
 * @property {string} name
 * @property {string} description
 * @property {number} price
 */

/**
 * @typedef {Object} InventoryDashboard
 * @property {number} cakes
 * @property {number} decorations
 * @property {number} ingredients
 * @property {Object} statistics
 * @property {number} statistics.totalOrders
 * @property {number} statistics.totalRevenue
 * @property {string} statistics.mostPopularCake
 */

/**
 * @typedef {Object} SalesReport
 * @property {number} totalSales
 * @property {Object[]} salesByCakeType
 * @property {string} salesByCakeType.cakeType
 * @property {number} salesByCakeType.sales
 * @property {Object[]} salesByDate
 * @property {string} salesByDate.date
 * @property {number} salesByDate.sales
 */

/**
 * @typedef {Object} InventoryReport
 * @property {number} totalInventory
 * @property {Object[]} inventoryByIngredient
 * @property {string} inventoryByIngredient.ingredient
 * @property {number} inventoryByIngredient.quantity
 * @property {Object[]} inventoryBySupplier
 * @property {string} inventoryBySupplier.supplier
 * @property {number} inventoryBySupplier.quantity
 */

const InventoryManagementPage = () => {
  const [cakes, setCakes] = useState([]);
  const [filteredCakes, setFilteredCakes] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCake, setSelectedCake] = useState(null);
  const [cakeQuantity, setCakeQuantity] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inventoryDashboard, setInventoryDashboard] = useState(null);
  const [salesReport, setSalesReport] = useState(null);
  const [inventoryReport, setInventoryReport] = useState(null);

  const axiosInstance = axios.create({
    baseURL: 'http://localhost:5000',
  });

  const fetchCakes = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/cakes');
      setCakes(response.data.cakes);
      setFilteredCakes(response.data.cakes);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchCakeDetails = useCallback(async (cakeId) => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(`/api/cakes/${cakeId}`);
      setSelectedCake(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchInventoryDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/inventory/dashboard');
      setInventoryDashboard(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchSalesReport = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/reports/sales');
      setSalesReport(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const fetchInventoryReport = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/api/reports/inventory');
      setInventoryReport(response.data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
    const filteredCakes = cakes.filter((cake) =>
      cake.name.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredCakes(filteredCakes);
  }, [cakes]);

  const handleFilter = useCallback((filter) => {
    const filteredCakes = cakes.filter((cake) => cake.type === filter);
    setFilteredCakes(filteredCakes);
  }, [cakes]);

  const handleSort = useCallback((sort) => {
    const sortedCakes = [...filteredCakes];
    sortedCakes.sort((a, b) => {
      if (sort === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sort === 'price') {
        return a.price - b.price;
      }
    });
    setFilteredCakes(sortedCakes);
  }, [filteredCakes]);

  const handleAddCake = useCallback(async (cake) => {
    try {
      setLoading(true);
      const response = await axiosInstance.post('/api/cakes', cake);
      setCakes([...cakes, response.data]);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, cakes]);

  const handleRemoveCake = useCallback(async (cakeId) => {
    try {
      setLoading(true);
      await axiosInstance.delete(`/api/cakes/${cakeId}`);
      const updatedCakes = cakes.filter((cake) => cake.cakeId !== cakeId);
      setCakes(updatedCakes);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, cakes]);

  const handleUpdateCakeQuantity = useCallback(async (cakeId, quantity) => {
    try {
      setLoading(true);
      const response = await axiosInstance.put(`/api/cakes/${cakeId}/quantity`, {
        quantity,
      });
      const updatedCakes = cakes.map((cake) =>
        cake.cakeId === cakeId ? { ...cake, quantity: response.data.quantity } : cake
      );
      setCakes(updatedCakes);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, cakes]);

  const handleUpdateCakeDetails = useCallback(async (cakeId, details) => {
    try {
      setLoading(true);
      const response = await axiosInstance.put(`/api/cakes/${cakeId}`, details);
      const updatedCakes = cakes.map((cake) =>
        cake.cakeId === cakeId ? { ...cake, ...response.data } : cake
      );
      setCakes(updatedCakes);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, cakes]);

  const handleMarkCakeAsOutOfStock = useCallback(async (cakeId) => {
    try {
      setLoading(true);
      await axiosInstance.put(`/api/cakes/${cakeId}/availability`, {
        availability: 'out of stock',
      });
      const updatedCakes = cakes.map((cake) =>
        cake.cakeId === cakeId ? { ...cake, availability: 'out of stock' } : cake
      );
      setCakes(updatedCakes);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [axiosInstance, cakes]);

  useEffect(() => {
    fetchCakes();
    fetchInventoryDashboard();
    fetchSalesReport();
    fetchInventoryReport();
  }, [fetchCakes, fetchInventoryDashboard, fetchSalesReport, fetchInventoryReport]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Inventory Management Page</h1>
      <input
        type="search"
        value={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
        placeholder="Search cakes"
      />
      <select onChange={(e) => handleFilter(e.target.value)}>
        <option value="">All</option>
        <option value="birthday">Birthday</option>
        <option value="wedding">Wedding</option>
      </select>
      <select onChange={(e) => handleSort(e.target.value)}>
        <option value="">None</option>
        <option value="name">Name</option>
        <option value="price">Price</option>
      </select>
      <ul>
        {filteredCakes.map((cake) => (
          <li key={cake.cakeId}>
            <h2>{cake.name}</h2>
            <p>{cake.description}</p>
            <p>Price: {cake.price}</p>
            <p>Quantity: {cake.quantity}</p>
            <button onClick={() => handleRemoveCake(cake.cakeId)}>Remove</button>
            <button onClick={() => handleUpdateCakeQuantity(cake.cakeId, cake.quantity + 1)}>
              Increase Quantity
            </button>
            <button onClick={() => handleUpdateCakeQuantity(cake.cakeId, cake.quantity - 1)}>
              Decrease Quantity
            </button>
            <button onClick={() => handleMarkCakeAsOutOfStock(cake.cakeId)}>Mark as Out of Stock</button>
          </li>
        ))}
      </ul>
      {selectedCake && (
        <div>
          <h2>{selectedCake.name}</h2>
          <p>{selectedCake.description}</p>
          <p>Price: {selectedCake.price}</p>
          <p>Quantity: {selectedCake.quantity}</p>
          <button onClick={() => handleUpdateCakeDetails(selectedCake.cakeId, { price: 10 })}>
            Update Price
          </button>
        </div>
      )}
      <button onClick={() => handleAddCake({ name: 'New Cake', description: 'New cake description', price: 10 })}>
        Add New Cake
      </button>
      {inventoryDashboard && (
        <div>
          <h2>Inventory Dashboard</h2>
          <p>Cakes: {inventoryDashboard.cakes}</p>
          <p>Decorations: {inventoryDashboard.decorations}</p>
          <p>Ingredients: {inventoryDashboard.ingredients}</p>
        </div>
      )}
      {salesReport && (
        <div>
          <h2>Sales Report</h2>
          <p>Total Sales: {salesReport.totalSales}</p>
          <ul>
            {salesReport.salesByCakeType.map((sale) => (
              <li key={sale.cakeType}>
                <p>{sale.cakeType}: {sale.sales}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
      {inventoryReport && (
        <div>
          <h2>Inventory Report</h2>
          <p>Total Inventory: {inventoryReport.totalInventory}</p>
          <ul>
            {inventoryReport.inventoryByIngredient.map((ingredient) => (
              <li key={ingredient.ingredient}>
                <p>{ingredient.ingredient}: {ingredient.quantity}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default InventoryManagementPage;
