# React Frontend

This project was automatically generated based on your application design.

## Pages Created

1. **Home Page** - Introduction to the online cake ordering platform
2. **Menu Page** - Browse available cakes with descriptions and prices
3. **Cake Customization Page** - Customize cake with flavors, designs, and messages
4. **Cart Page** - View selected cakes and proceed to checkout
5. **Checkout Page** - Specify pickup or delivery options and payment details
6. **Payment Page** - Complete payment using a dummy payment gateway
7. **Order Confirmation Page** - Display order summary and confirmation
8. **Login Page** - User authentication
9. **Registration Page** - Create a new user account
10. **Account Dashboard** - View order history and account information
11. **Order History Page** - Detailed view of past orders
12. **Admin Dashboard** - Restaurant administration and order management
13. **POS Integration Page** - Integration with the restaurant's existing POS system
14. **Inventory Management Page** - Manage cake inventory and availability
15. **Contact Page** - Get in touch with the restaurant for inquiries and support

## Getting Started

1. Navigate to the project directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Backend Integration

The frontend is configured to communicate with the Flask backend at `http://localhost:5000`.
Make sure the backend is running before testing API integrations.

## Project Structure

```
frontend/
├── src/
│   ├── pages/          # All page components
│   ├── App.js          # Main app with routing
│   └── App.css         # Global styles
└── package.json
```

## Next Steps

- Implement the TODO comments in each page component
- Connect to backend API endpoints
- Add state management (Redux, Context API, etc.) if needed
- Implement authentication flows
- Add form validation
- Style components according to your design system
