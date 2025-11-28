import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Import all page components
import HomePage from './pages/HomePage';
import MenuPage from './pages/MenuPage';
import CakeCustomizationPage from './pages/CakeCustomizationPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import PaymentPage from './pages/PaymentPage';
import OrderConfirmationPage from './pages/OrderConfirmationPage';
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import AccountDashboard from './pages/AccountDashboard';
import OrderHistoryPage from './pages/OrderHistoryPage';
import AdminDashboard from './pages/AdminDashboard';
import PosIntegrationPage from './pages/PosIntegrationPage';
import InventoryManagementPage from './pages/InventoryManagementPage';
import ContactPage from './pages/ContactPage';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h2>Application Navigation</h2>
          <ul>
            <li><Link to="/home-page">Home Page</Link></li>
            <li><Link to="/menu-page">Menu Page</Link></li>
            <li><Link to="/cake-customization-page">Cake Customization Page</Link></li>
            <li><Link to="/cart-page">Cart Page</Link></li>
            <li><Link to="/checkout-page">Checkout Page</Link></li>
            <li><Link to="/payment-page">Payment Page</Link></li>
            <li><Link to="/order-confirmation-page">Order Confirmation Page</Link></li>
            <li><Link to="/login-page">Login Page</Link></li>
            <li><Link to="/registration-page">Registration Page</Link></li>
            <li><Link to="/account-dashboard">Account Dashboard</Link></li>
            <li><Link to="/order-history-page">Order History Page</Link></li>
            <li><Link to="/admin-dashboard">Admin Dashboard</Link></li>
            <li><Link to="/pos-integration-page">POS Integration Page</Link></li>
            <li><Link to="/inventory-management-page">Inventory Management Page</Link></li>
            <li><Link to="/contact-page">Contact Page</Link></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/home-page" element={<HomePage />} />
            <Route path="/menu-page" element={<MenuPage />} />
            <Route path="/cake-customization-page" element={<CakeCustomizationPage />} />
            <Route path="/cart-page" element={<CartPage />} />
            <Route path="/checkout-page" element={<CheckoutPage />} />
            <Route path="/payment-page" element={<PaymentPage />} />
            <Route path="/order-confirmation-page" element={<OrderConfirmationPage />} />
            <Route path="/login-page" element={<LoginPage />} />
            <Route path="/registration-page" element={<RegistrationPage />} />
            <Route path="/account-dashboard" element={<AccountDashboard />} />
            <Route path="/order-history-page" element={<OrderHistoryPage />} />
            <Route path="/admin-dashboard" element={<AdminDashboard />} />
            <Route path="/pos-integration-page" element={<PosIntegrationPage />} />
            <Route path="/inventory-management-page" element={<InventoryManagementPage />} />
            <Route path="/contact-page" element={<ContactPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
