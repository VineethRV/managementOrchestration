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
 * @typedef {Object} CakeCategory
 * @property {number} id
 * @property {string} name
 * @property {string} description
 */

/**
 * MenuPage Component
 * @returns {JSX.Element}
 */
function MenuPage() {
  const [cakes, setCakes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState({ priceRange: { min: 0, max: 100 }, flavor: '', popularity: '' });
  const [pageNumber, setPageNumber] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cart, setCart] = useState([]);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const baseUrl = 'http://localhost:5000';

  const fetchCakes = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${baseUrl}/api/cakes/page/${pageNumber}`);
      setCakes(response.data.cakes);
      setTotalPages(response.data.totalPages);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [baseUrl, pageNumber]);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await axios.get(`${baseUrl}/api/cake-categories`);
      setCategories(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  const handleSearch = useCallback(async (query) => {
    try {
      const response = await axios.get(`${baseUrl}/api/cakes/search`, { params: { query } });
      setCakes(response.data.cakes);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  const handleFilter = useCallback(async (filter) => {
    try {
      const response = await axios.get(`${baseUrl}/api/cakes/filter`, { params: filter });
      setCakes(response.data.cakes);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  const handleAddToCart = useCallback(async (cakeId, quantity, customizations) => {
    try {
      const response = await axios.post(`${baseUrl}/api/cart`, { cakeId, quantity, customizations });
      setCart(response.data.cartItems);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  const handleLogin = useCallback(async (username, password) => {
    try {
      const response = await axios.post(`${baseUrl}/api/login`, { username, password });
      setIsLoggedIn(true);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  const handleCreateAccount = useCallback(async (name, email, password, phone) => {
    try {
      const response = await axios.post(`${baseUrl}/api/accounts`, { name, email, password, phone });
      setIsLoggedIn(true);
    } catch (error) {
      setError(error.message);
    }
  }, [baseUrl]);

  useEffect(() => {
    fetchCakes();
    fetchCategories();
  }, [fetchCakes, fetchCategories]);

  const handlePageChange = (pageNumber) => {
    setPageNumber(pageNumber);
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilter((prevFilter) => ({ ...prevFilter, [name]: value }));
  };

  const handleAddToCartClick = (cakeId, quantity, customizations) => {
    handleAddToCart(cakeId, quantity, customizations);
  };

  const handleLoginClick = (username, password) => {
    handleLogin(username, password);
  };

  const handleCreateAccountClick = (name, email, password, phone) => {
    handleCreateAccount(name, email, password, phone);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Menu Page</h1>
      <input
        type="search"
        value={searchQuery}
        onChange={handleSearchChange}
        placeholder="Search for cakes"
      />
      <button onClick={() => handleSearch(searchQuery)}>Search</button>
      <div>
        <h2>Filter by:</h2>
        <label>
          Price Range:
          <input
            type="number"
            name="priceRange.min"
            value={filter.priceRange.min}
            onChange={handleFilterChange}
          />
          -
          <input
            type="number"
            name="priceRange.max"
            value={filter.priceRange.max}
            onChange={handleFilterChange}
          />
        </label>
        <label>
          Flavor:
          <select name="flavor" value={filter.flavor} onChange={handleFilterChange}>
            <option value="">Select flavor</option>
            <option value="chocolate">Chocolate</option>
            <option value="vanilla">Vanilla</option>
          </select>
        </label>
        <label>
          Popularity:
          <select name="popularity" value={filter.popularity} onChange={handleFilterChange}>
            <option value="">Select popularity</option>
            <option value="most popular">Most popular</option>
            <option value="least popular">Least popular</option>
          </select>
        </label>
        <button onClick={() => handleFilter(filter)}>Filter</button>
      </div>
      <div>
        <h2>Cake Categories:</h2>
        <ul>
          {categories.map((category) => (
            <li key={category.id}>
              <a href={`#${category.name}`}>{category.name}</a>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Cakes:</h2>
        <ul>
          {cakes.map((cake) => (
            <li key={cake.cakeId}>
              <h3>{cake.name}</h3>
              <p>{cake.description}</p>
              <p>Price: ${cake.price}</p>
              <button onClick={() => handleAddToCartClick(cake.cakeId, 1, {})}>
                Add to Cart
              </button>
              <button>View Details</button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Cart:</h2>
        <ul>
          {cart.map((item) => (
            <li key={item.cakeId}>
              <h3>{item.name}</h3>
              <p>Quantity: {item.quantity}</p>
              <p>Customizations: {item.customizations}</p>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Login:</h2>
        <form>
          <label>
            Username:
            <input type="text" name="username" />
          </label>
          <label>
            Password:
            <input type="password" name="password" />
          </label>
          <button onClick={(event) => {
            event.preventDefault();
            handleLoginClick(event.target.username.value, event.target.password.value);
          }}>
            Login
          </button>
        </form>
      </div>
      <div>
        <h2>Create Account:</h2>
        <form>
          <label>
            Name:
            <input type="text" name="name" />
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
            Phone:
            <input type="text" name="phone" />
          </label>
          <button onClick={(event) => {
            event.preventDefault();
            handleCreateAccountClick(event.target.name.value, event.target.email.value, event.target.password.value, event.target.phone.value);
          }}>
            Create Account
          </button>
        </form>
      </div>
      <div>
        <h2>Pagination:</h2>
        <button onClick={() => handlePageChange(pageNumber - 1)}>Previous</button>
        <span>Page {pageNumber} of {totalPages}</span>
        <button onClick={() => handlePageChange(pageNumber + 1)}>Next</button>
      </div>
    </div>
  );
}

export default MenuPage;
