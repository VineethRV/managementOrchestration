# Flask Backend API

This Flask backend was automatically generated based on your application design.

## Endpoints Created

1. **GET /api/cakes** - Get Cakes
2. **GET /api/cakes/search** - Search Cakes
3. **GET /api/cakes/{cakeId}** - Get Cake Details
4. **POST /api/orders** - Create Order
5. **GET /api/orders/options** - Get Pickup and Delivery Options
6. **POST /api/orders/{orderId}/payment** - Process Payment
7. **POST /api/users** - Create Account
8. **POST /api/users/login** - Login
9. **GET /api/users/{userId}/orders** - Get Order History
10. **GET /api/restaurant/info** - Get Restaurant Info
11. **GET /api/cakes/filter** - Filter Cakes
12. **GET /api/cake-categories** - Get Cake Categories
13. **POST /api/cart** - Add Cake to Cart
14. **GET /api/cart** - Get Cart
15. **POST /api/accounts** - Create Account
16. **POST /api/login** - Login
17. **GET /api/cakes/page/{pageNumber}** - Get Paginated Cakes
18. **GET /api/cake-options** - Get Cake Options
19. **GET /api/cake-flavors** - Get Cake Flavors
20. **GET /api/cake-designs** - Get Cake Designs
21. **POST /api/custom-cake** - Create Custom Cake
22. **GET /api/pickup-options** - Get Pickup Options
23. **GET /api/delivery-options** - Get Delivery Options
24. **POST /api/validate-address** - Validate Address
25. **POST /api/calculate-total-cost** - Calculate Total Cost
26. **POST /api/add-to-cart** - Add to Cart
27. **POST /api/proceed-to-payment** - Proceed to Payment
28. **POST /api/process-payment** - Process Payment
29. **POST /api/create-account** - Create Account
30. **GET /api/order-history** - Get Order History
31. **GET /api/cart/items** - Get Cart Items
32. **PUT /api/cart/items/{itemId}/quantity** - Update Cart Item Quantity
33. **DELETE /api/cart/items/{itemId}** - Remove Cart Item
34. **GET /api/cart/total-cost** - Get Total Cost
35. **GET /api/cart/pickup-delivery-options** - Get Pickup and Delivery Options
36. **POST /api/cart/promo-code** - Apply Promo Code
37. **GET /api/cart/order-summary** - Get Order Summary
38. **POST /api/cart/checkout** - Proceed to Checkout
39. **POST /api/cart/payment** - Process Payment
40. **POST /api/cart/payment/validate** - Validate Payment
41. **GET /api/checkout/options** - Get Pickup and Delivery Options
42. **GET /api/checkout/payment-methods** - Get Payment Method Options
43. **POST /api/checkout/orders** - Create Order
44. **POST /api/checkout/payment-details/validate** - Validate Payment Details
45. **POST /api/checkout/payment/process** - Process Payment
46. **GET /api/checkout/orders/summary** - Get Order Summary
47. **PUT /api/checkout/orders/status** - Update Order Status
48. **POST /api/customers** - Create Customer Account
49. **POST /api/customers/login** - Login Customer
50. **GET /api/customers/orders** - Get Order History
51. **POST /api/checkout/orders/calculate-taxes** - Calculate Taxes and Fees
52. **GET /api/payment-methods** - Get Payment Methods
53. **GET /api/orders/summary** - Get Order Summary
54. **POST /api/payments** - Process Payment
55. **POST /api/users/payment-info** - Save Payment Information
56. **POST /api/auth/login** - Login
57. **POST /api/auth/register** - Create Account
58. **GET /api/payments/verify** - Verify Payment
59. **GET /api/orders/{orderId}** - Get Order Details
60. **GET /api/orders/{orderId}/pickup-delivery** - Get Order Pickup or Delivery Details
61. **GET /api/orders/{orderId}/payment** - Get Order Payment Details
62. **GET /api/orders/{orderId}/confirmation-number** - Get Order Confirmation Number
63. **GET /api/users/{userId}/order-history** - Get Order History
64. **GET /api/orders/{orderId}/receipt** - Generate Receipt
65. **GET /api/restaurant/contact-info** - Get Restaurant Contact Information
66. **GET /api/restaurant/social-media-links** - Get Restaurant Social Media Links
67. **POST /api/auth/forgot-password** - Forgot Password
68. **POST /api/auth/validate-credentials** - Validate Credentials
69. **POST /api/auth/save-credentials** - Save Login Credentials
70. **DELETE /api/auth/clear-credentials** - Clear Login Credentials
71. **GET /api/registration/form** - Get Registration Form
72. **POST /api/registration/validate** - Validate Registration Form
73. **GET /api/registration/username/:username** - Check Username Availability
74. **GET /api/registration/email/:email** - Check Email Availability
75. **POST /api/registration** - Create New User
76. **GET /api/terms-and-conditions** - Get Terms and Conditions
77. **GET /api/login** - Get Login Page
78. **GET /api/account** - Get Account Information
79. **GET /api/orders** - Get Order History
80. **GET /api/orders/search** - Search Orders
81. **POST /api/orders/{orderId}/reorder** - Re-order Cake
82. **GET /api/account/loyalty** - Get Loyalty Points
83. **PUT /api/account** - Update Account Information
84. **PUT /api/account/password** - Update Password
85. **POST /api/logout** - Logout
86. **GET /api/orders/recent** - Get Recent Orders
87. **GET /api/orders/filter** - Filter Orders
88. **GET /api/customers/me** - Get Customer Information
89. **GET /api/admin/sales-metrics** - Get Sales Metrics
90. **GET /api/admin/orders** - Get Orders
91. **GET /api/admin/orders/search** - Search Orders
92. **PUT /api/admin/orders/{orderId}** - Update Order Status
93. **GET /api/admin/calendar** - Get Calendar View
94. **GET /api/admin/low-stock-alerts** - Get Low-Stock Alerts
95. **GET /api/admin/cake-menu-items** - Get Cake Menu Items
96. **POST /api/admin/cake-menu-items** - Add Cake Menu Item
97. **PUT /api/admin/cake-menu-items/{menuItemId}** - Update Cake Menu Item
98. **DELETE /api/admin/cake-menu-items/{menuItemId}** - Delete Cake Menu Item
99. **GET /api/admin/customers** - Get Customer Accounts
100. **GET /api/admin/customers/{customerId}/order-history** - Get Customer Order History
101. **GET /api/admin/payment-metrics** - Get Payment Metrics
102. **GET /api/admin/restaurant-settings** - Get Restaurant Settings
103. **PUT /api/admin/restaurant-settings** - Update Restaurant Settings
104. **POST /api/admin/integrate-pos-system** - Integrate with POS System
105. **GET /api/pos/systems** - Get Available POS Systems
106. **POST /api/pos/connect** - Connect to POS System
107. **POST /api/pos/disconnect** - Disconnect from POS System
108. **GET /api/pos/status** - Get POS System Integration Status
109. **PUT /api/pos/inventory** - Update Cake Inventory
110. **PUT /api/pos/override** - Override POS System Data
111. **GET /api/pos/history** - Get POS System Connection History
112. **POST /api/pos/error** - Handle POS System Error
113. **GET /api/pos/credentials** - Get POS System Credentials
114. **PUT /api/pos/credentials** - Update POS System Credentials
115. **POST /api/cakes** - Add Cake to Inventory
116. **DELETE /api/cakes/{cakeId}** - Remove Cake from Inventory
117. **PUT /api/cakes/{cakeId}/quantity** - Update Cake Quantity
118. **PUT /api/cakes/{cakeId}** - Update Cake Details
119. **GET /api/cakes/low-stock** - Get Low Stock Cakes
120. **PUT /api/cakes/{cakeId}/availability** - Update Cake Availability
121. **GET /api/inventory/dashboard** - Get Inventory Dashboard
122. **GET /api/reports/sales** - Generate Sales Report
123. **GET /api/reports/inventory** - Generate Inventory Report
124. **GET /api/contact-info** - Get Contact Information
125. **GET /api/business-hours** - Get Business Hours
126. **GET /api/social-media** - Get Social Media Profiles
127. **GET /api/faq** - Get FAQ
128. **POST /api/contact-form** - Submit Contact Form
129. **POST /api/upload-file** - Upload File
130. **GET /api/restaurant-location** - Get Restaurant Location

## Getting Started

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate virtual environment:
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **Mac/Linux:**
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask server:
   ```bash
   python app.py
   ```

5. API will be available at [http://localhost:5000](http://localhost:5000)

## API Documentation

Visit `http://localhost:5000/` to see a list of all available endpoints.

## Project Structure

```
backend/
├── venv/              # Virtual environment
├── app.py             # Main Flask application
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Next Steps

- Implement the TODO comments in each endpoint
- Add database integration (SQLAlchemy recommended)
- Add authentication/authorization (JWT, Flask-Login, etc.)
- Add input validation
- Add logging
- Write unit tests
- Set up database migrations
- Add API documentation (Swagger/OpenAPI)

## CORS Configuration

CORS is enabled for `http://localhost:3000` to allow the React frontend to communicate with this backend.
Update the CORS configuration in `app.py` if your frontend runs on a different port.

## Environment Variables

Configure your environment in the `.env` file:
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (if using a database)
