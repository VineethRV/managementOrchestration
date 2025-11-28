
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    order_status = db.Column(db.String(100), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

class CakeMenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cake_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    order_history = db.relationship('Order', backref='customer', lazy=True)

class RestaurantSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_hours = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)

# Routes
@app.route('/api/admin/sales-metrics', methods=['GET'])
@jwt_required()
def get_sales_metrics():
    """
    Retrieve overall sales and revenue metrics.
    
    Returns:
        dict: Sales metrics.
    """
    try:
        total_orders = Order.query.count()
        total_revenue = sum([order.total_cost for order in Order.query.all()])
        online_orders = sum([order.total_cost for order in Order.query.filter_by(order_status='online').all()])
        in_store_orders = sum([order.total_cost for order in Order.query.filter_by(order_status='in_store').all()])
        pending_orders = Order.query.filter_by(order_status='pending').count()
        in_progress_orders = Order.query.filter_by(order_status='in_progress').count()
        completed_orders = Order.query.filter_by(order_status='completed').count()
        
        return jsonify({
            'sales': {
                'total_orders': total_orders,
                'total_revenue': total_revenue
            },
            'revenue_breakdown': {
                'online_orders': online_orders,
                'in_store_orders': in_store_orders
            },
            'order_status': {
                'pending': pending_orders,
                'in_progress': in_progress_orders,
                'completed': completed_orders
            }
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """
    List all current and pending orders with order status.
    
    Returns:
        dict: Orders.
    """
    try:
        orders = Order.query.all()
        return jsonify({
            'orders': [
                {
                    'order_id': order.id,
                    'customer_name': order.customer_name,
                    'order_date': order.order_date,
                    'order_status': order.order_status,
                    'total_cost': order.total_cost
                } for order in orders
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/orders/search', methods=['GET'])
@jwt_required()
def search_orders():
    """
    Find specific orders by customer name, order ID, or date.
    
    Returns:
        dict: Orders.
    """
    try:
        customer_name = request.args.get('customer_name')
        order_id = request.args.get('order_id')
        date = request.args.get('date')
        
        if customer_name:
            orders = Order.query.filter_by(customer_name=customer_name).all()
        elif order_id:
            orders = Order.query.filter_by(id=order_id).all()
        elif date:
            orders = Order.query.filter_by(order_date=date).all()
        else:
            return jsonify({'message': 'Invalid search parameters'}), 400
        
        return jsonify({
            'orders': [
                {
                    'order_id': order.id,
                    'customer_name': order.customer_name,
                    'order_date': order.order_date,
                    'order_status': order.order_status,
                    'total_cost': order.total_cost
                } for order in orders
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """
    Update order status and add notes to orders.
    
    Args:
        order_id (int): Order ID.
    
    Returns:
        dict: Updated order.
    """
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'message': 'Order not found'}), 404
        
        data = request.get_json()
        if 'order_status' in data:
            order.order_status = data['order_status']
        if 'notes' in data:
            order.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'order_id': order.id,
            'order_status': order.order_status,
            'notes': order.notes
        }), 200
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/calendar', methods=['GET'])
@jwt_required()
def get_calendar_view():
    """
    Display a calendar view of upcoming orders and pickups.
    
    Returns:
        dict: Calendar view.
    """
    try:
        orders = Order.query.all()
        return jsonify({
            'calendar': {
                'upcoming_orders': [
                    {
                        'order_id': order.id,
                        'order_date': order.order_date,
                        'pickup_time': order.pickup_time
                    } for order in orders
                ]
            }
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/low-stock-alerts', methods=['GET'])
@jwt_required()
def get_low_stock_alerts():
    """
    Show low-stock alerts for cake ingredients and decorations.
    
    Returns:
        dict: Low stock alerts.
    """
    try:
        # Assuming there's a CakeIngredient model
        cake_ingredients = CakeIngredient.query.all()
        return jsonify({
            'low_stock_alerts': [
                {
                    'ingredient': ingredient.name,
                    'quantity': ingredient.quantity
                } for ingredient in cake_ingredients if ingredient.quantity < 10
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/cake-menu-items', methods=['GET'])
@jwt_required()
def get_cake_menu_items():
    """
    Retrieve cake menu items.
    
    Returns:
        dict: Cake menu items.
    """
    try:
        cake_menu_items = CakeMenuItem.query.all()
        return jsonify({
            'cake_menu_items': [
                {
                    'menu_item_id': item.id,
                    'cake_name': item.cake_name,
                    'description': item.description,
                    'price': item.price
                } for item in cake_menu_items
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/cake-menu-items', methods=['POST'])
@jwt_required()
def add_cake_menu_item():
    """
    Add a new cake menu item.
    
    Returns:
        dict: Added cake menu item.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request'}), 400
        
        cake_name = data.get('cake_name')
        description = data.get('description')
        price = data.get('price')
        
        if not cake_name or not description or not price:
            return jsonify({'message': 'Invalid request'}), 400
        
        cake_menu_item = CakeMenuItem(cake_name=cake_name, description=description, price=price)
        db.session.add(cake_menu_item)
        db.session.commit()
        
        return jsonify({
            'menu_item_id': cake_menu_item.id,
            'cake_name': cake_menu_item.cake_name,
            'description': cake_menu_item.description,
            'price': cake_menu_item.price
        }), 201
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/cake-menu-items/<int:menu_item_id>', methods=['PUT'])
@jwt_required()
def update_cake_menu_item(menu_item_id):
    """
    Update an existing cake menu item.
    
    Args:
        menu_item_id (int): Menu item ID.
    
    Returns:
        dict: Updated cake menu item.
    """
    try:
        cake_menu_item = CakeMenuItem.query.get(menu_item_id)
        if not cake_menu_item:
            return jsonify({'message': 'Menu item not found'}), 404
        
        data = request.get_json()
        if 'cake_name' in data:
            cake_menu_item.cake_name = data['cake_name']
        if 'description' in data:
            cake_menu_item.description = data['description']
        if 'price' in data:
            cake_menu_item.price = data['price']
        
        db.session.commit()
        
        return jsonify({
            'menu_item_id': cake_menu_item.id,
            'cake_name': cake_menu_item.cake_name,
            'description': cake_menu_item.description,
            'price': cake_menu_item.price
        }), 200
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/cake-menu-items/<int:menu_item_id>', methods=['DELETE'])
@jwt_required()
def delete_cake_menu_item(menu_item_id):
    """
    Remove a cake menu item.
    
    Args:
        menu_item_id (int): Menu item ID.
    
    Returns:
        dict: Message.
    """
    try:
        cake_menu_item = CakeMenuItem.query.get(menu_item_id)
        if not cake_menu_item:
            return jsonify({'message': 'Menu item not found'}), 404
        
        db.session.delete(cake_menu_item)
        db.session.commit()
        
        return jsonify({'message': 'Menu item deleted successfully'}), 200
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """
    Retrieve customer accounts and order history.
    
    Returns:
        dict: Customers.
    """
    try:
        customers = Customer.query.all()
        return jsonify({
            'customers': [
                {
                    'customer_id': customer.id,
                    'customer_name': customer.customer_name,
                    'order_history': [
                        {
                            'order_id': order.id,
                            'order_date': order.order_date
                        } for order in customer.order_history
                    ]
                } for customer in customers
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/customers/<int:customer_id>/order-history', methods=['GET'])
@jwt_required()
def get_customer_order_history(customer_id):
    """
    Retrieve order history for a specific customer.
    
    Args:
        customer_id (int): Customer ID.
    
    Returns:
        dict: Order history.
    """
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'message': 'Customer not found'}), 404
        
        return jsonify({
            'order_history': [
                {
                    'order_id': order.id,
                    'order_date': order.order_date
                } for order in customer.order_history
            ]
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/payment-metrics', methods=['GET'])
@jwt_required()
def get_payment_metrics():
    """
    Retrieve payment processing metrics.
    
    Returns:
        dict: Payment metrics.
    """
    try:
        # Assuming there's a Payment model
        payments = Payment.query.all()
        total_payments = sum([payment.amount for payment in payments])
        credit_card_payments = sum([payment.amount for payment in payments if payment.method == 'credit_card'])
        paypal_payments = sum([payment.amount for payment in payments if payment.method == 'paypal'])
        
        return jsonify({
            'payment_metrics': {
                'total_payments': total_payments,
                'payment_methods': {
                    'credit_card': credit_card_payments,
                    'paypal': paypal_payments
                }
            }
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/restaurant-settings', methods=['GET'])
@jwt_required()
def get_restaurant_settings():
    """
    Retrieve restaurant settings.
    
    Returns:
        dict: Restaurant settings.
    """
    try:
        restaurant_settings = RestaurantSetting.query.first()
        if not restaurant_settings:
            return jsonify({'message': 'Restaurant settings not found'}), 404
        
        return jsonify({
            'restaurant_settings': {
                'business_hours': restaurant_settings.business_hours,
                'contact_info': restaurant_settings.contact_info
            }
        }), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/restaurant-settings', methods=['PUT'])
@jwt_required()
def update_restaurant_settings():
    """
    Update restaurant settings.
    
    Returns:
        dict: Updated restaurant settings.
    """
    try:
        restaurant_settings = RestaurantSetting.query.first()
        if not restaurant_settings:
            return jsonify({'message': 'Restaurant settings not found'}), 404
        
        data = request.get_json()
        if 'business_hours' in data:
            restaurant_settings.business_hours = data['business_hours']
        if 'contact_info' in data:
            restaurant_settings.contact_info = data['contact_info']
        
        db.session.commit()
        
        return jsonify({
            'restaurant_settings': {
                'business_hours': restaurant_settings.business_hours,
                'contact_info': restaurant_settings.contact_info
            }
        }), 200
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/admin/integrate-pos-system', methods=['POST'])
@jwt_required()
def integrate_pos_system():
    """
    Integrate with POS system to automatically update inventory levels.
    
    Returns:
        dict: Message.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request'}), 400
        
        pos_system_api_key = data.get('pos_system_api_key')
        if not pos_system_api_key:
            return jsonify({'message': 'Invalid request'}), 400
        
        # Integrate with POS system using the provided API key
        # ...
        
        return jsonify({'message': 'POS system integrated successfully'}), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
