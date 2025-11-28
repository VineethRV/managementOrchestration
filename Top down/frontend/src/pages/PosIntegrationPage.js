import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} PosSystem
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {string} api_key
 * @property {Object} credentials
 */

/**
 * @typedef {Object} PosSystemCredentials
 * @property {string} api_key
 * @property {Object} credentials
 */

/**
 * @typedef {Object} CakeInventory
 * @property {string} cake_id
 * @property {number} quantity
 */

/**
 * @typedef {Object} PosSystemStatus
 * @property {boolean} connected
 * @property {string} pos_system_id
 * @property {Array<Object>} connection_history
 */

const PosIntegrationPage = () => {
  const [posSystems, setPosSystems] = useState([]);
  const [selectedPosSystem, setSelectedPosSystem] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [cakeInventory, setCakeInventory] = useState([]);
  const [overrideCakeInventory, setOverrideCakeInventory] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const axiosInstance = useMemo(() => {
    return axios.create({
      baseURL: 'http://localhost:5000',
    });
  }, []);

  const getPosSystems = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/pos/systems');
      setPosSystems(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const connectToPosSystem = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/pos/connect', {
        api_key: apiKey,
        credentials: credentials,
      });
      setConnectionStatus(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, apiKey, credentials]);

  const disconnectFromPosSystem = useCallback(async () => {
    try {
      const response = await axiosInstance.post('/api/pos/disconnect');
      setConnectionStatus(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const getPosSystemStatus = useCallback(async () => {
    try {
      const response = await axiosInstance.get('/api/pos/status');
      setConnectionStatus(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance]);

  const updateCakeInventory = useCallback(async () => {
    try {
      const response = await axiosInstance.put('/api/pos/inventory', {
        inventory: cakeInventory,
      });
      setCakeInventory(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, cakeInventory]);

  const overridePosSystemData = useCallback(async () => {
    try {
      const response = await axiosInstance.put('/api/pos/override', {
        cake_id: overrideCakeInventory.cake_id,
        quantity: overrideCakeInventory.quantity,
        availability: overrideCakeInventory.availability,
      });
      setOverrideCakeInventory(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, [axiosInstance, overrideCakeInventory]);

  useEffect(() => {
    getPosSystems();
  }, [getPosSystems]);

  const handleConnect = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await connectToPosSystem();
      await getPosSystemStatus();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await disconnectFromPosSystem();
      await getPosSystemStatus();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCakeInventory = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await updateCakeInventory();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOverridePosSystemData = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await overridePosSystemData();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>POS Integration Page</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          <h2>Available POS Systems</h2>
          <ul>
            {posSystems.map((posSystem) => (
              <li key={posSystem.id}>
                {posSystem.name} ({posSystem.description})
              </li>
            ))}
          </ul>
          <form onSubmit={handleConnect}>
            <label>
              Select POS System:
              <select
                value={selectedPosSystem}
                onChange={(event) => setSelectedPosSystem(event.target.value)}
              >
                <option value="">Select a POS system</option>
                {posSystems.map((posSystem) => (
                  <option key={posSystem.id} value={posSystem.id}>
                    {posSystem.name}
                  </option>
                ))}
              </select>
            </label>
            <br />
            <label>
              API Key:
              <input
                type="text"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
              />
            </label>
            <br />
            <label>
              Credentials:
              <input
                type="text"
                value={credentials.username}
                onChange={(event) =>
                  setCredentials({ ...credentials, username: event.target.value })
                }
                placeholder="Username"
              />
              <input
                type="password"
                value={credentials.password}
                onChange={(event) =>
                  setCredentials({ ...credentials, password: event.target.value })
                }
                placeholder="Password"
              />
            </label>
            <br />
            <button type="submit">Connect</button>
          </form>
          {connectionStatus ? (
            <div>
              <h2>Connection Status</h2>
              <p>Connected: {connectionStatus.connected ? 'Yes' : 'No'}</p>
              <p>POS System ID: {connectionStatus.pos_system_id}</p>
              <button onClick={handleDisconnect}>Disconnect</button>
            </div>
          ) : null}
          <h2>Cake Inventory</h2>
          <form onSubmit={handleUpdateCakeInventory}>
            <label>
              Cake ID:
              <input
                type="text"
                value={cakeInventory.cake_id}
                onChange={(event) =>
                  setCakeInventory({ ...cakeInventory, cake_id: event.target.value })
                }
              />
            </label>
            <br />
            <label>
              Quantity:
              <input
                type="number"
                value={cakeInventory.quantity}
                onChange={(event) =>
                  setCakeInventory({ ...cakeInventory, quantity: event.target.value })
                }
              />
            </label>
            <br />
            <button type="submit">Update Cake Inventory</button>
          </form>
          <h2>Override POS System Data</h2>
          <form onSubmit={handleOverridePosSystemData}>
            <label>
              Cake ID:
              <input
                type="text"
                value={overrideCakeInventory.cake_id}
                onChange={(event) =>
                  setOverrideCakeInventory({
                    ...overrideCakeInventory,
                    cake_id: event.target.value,
                  })
                }
              />
            </label>
            <br />
            <label>
              Quantity:
              <input
                type="number"
                value={overrideCakeInventory.quantity}
                onChange={(event) =>
                  setOverrideCakeInventory({
                    ...overrideCakeInventory,
                    quantity: event.target.value,
                  })
                }
              />
            </label>
            <br />
            <label>
              Availability:
              <input
                type="checkbox"
                checked={overrideCakeInventory.availability}
                onChange={(event) =>
                  setOverrideCakeInventory({
                    ...overrideCakeInventory,
                    availability: event.target.checked,
                  })
                }
              />
            </label>
            <br />
            <button type="submit">Override POS System Data</button>
          </form>
          {error ? (
            <p style={{ color: 'red' }}>{error}</p>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default PosIntegrationPage;
