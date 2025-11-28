
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cake_type = db.Column(db.String(100), nullable=False)
    flavor = db.Column(db.String(100), nullable=False)
    design = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Cake('{self.cake_type}', '{self.flavor}', '{self.design}', '{self.message}')"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cake_id = db.Column(db.Integer, db.ForeignKey('cake.id'), nullable=False)
    cake = db.relationship('Cake', backref=db.backref('orders', lazy=True))
    pickup_or_delivery = db.Column(db.String(100), nullable=False)
    pickup_time = db.Column(db.DateTime, nullable=False)
    delivery_address = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Order('{self.cake_id}', '{self.pickup_or_delivery}', '{self.pickup_time}', '{self.delivery_address}', '{self.quantity}', '{self.total_cost}')"

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order = db.relationship('Order', backref=db.backref('payments', lazy=True))
    payment_method = db.Column(db.String(100), nullable=False)
    payment_status = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Payment('{self.order_id}', '{self.payment_method}', '{self.payment_status}')"

# Routes
@app.route('/api/orders', methods=['POST'])
def create_order():
    """
    Create a new order with cake customization options.
    
    :return: JSON response with order details
    """
    try:
        data = request.get_json()
        cake = Cake(cake_type=data['cake_type'], flavor=data['flavor'], design=data['design'], message=data['message'])
        db.session.add(cake)
        db.session.commit()
        order = Order(cake_id=cake.id, pickup_or_delivery=data['pickup_or_delivery'], pickup_time=datetime.strptime(data['pickup_time'], '%Y-%m-%d %H:%M:%S'), delivery_address=data['delivery_address'], quantity=data['quantity'], total_cost=data['quantity'] * 10.0)
        db.session.add(order)
        db.session.commit()
        return jsonify({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/options', methods=['GET'])
def get_pickup_and_delivery_options():
    """
    Retrieve available pickup and delivery options with associated costs and estimated times.
    
    :return: JSON response with pickup and delivery options
    """
    try:
        pickup_options = [{'option': 'Pickup', 'cost': 0.0, 'estimated_time': '30 minutes'}, {'option': 'Delivery', 'cost': 5.0, 'estimated_time': '1 hour'}]
        delivery_options = [{'option': 'Standard Delivery', 'cost': 5.0, 'estimated_time': '1 hour'}, {'option': 'Express Delivery', 'cost': 10.0, 'estimated_time': '30 minutes'}]
        return jsonify({'pickup_options': pickup_options, 'delivery_options': delivery_options}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/payment', methods=['POST'])
def process_payment(order_id):
    """
    Process payment for an order using a dummy payment gateway.
    
    :param order_id: Order ID
    :return: JSON response with payment status
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        data = request.get_json()
        payment = Payment(order_id=order_id, payment_method=data['payment_method'], payment_status='Success')
        db.session.add(payment)
        db.session.commit()
        return jsonify({'payment_status': payment.payment_status, 'payment_method': payment.payment_method, 'order_total': order.total_cost}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/summary', methods=['GET'])
def get_order_summary():
    """
    Retrieve order summary including cake details, pickup/delivery options, and total cost.
    
    :return: JSON response with order summary
    """
    try:
        orders = Order.query.all()
        order_summary = []
        for order in orders:
            cake = Cake.query.get(order.cake_id)
            order_summary.append({'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost})
        return jsonify({'order_summary': order_summary}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    """
    Retrieve order summary, including cake details, customization options, and quantity.
    
    :param order_id: Order ID
    :return: JSON response with order details
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        cake = Cake.query.get(order.cake_id)
        return jsonify({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/pickup-delivery', methods=['GET'])
def get_order_pickup_or_delivery_details(order_id):
    """
    Retrieve pickup or delivery details, including date, time, and location.
    
    :param order_id: Order ID
    :return: JSON response with pickup or delivery details
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify({'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/payment', methods=['GET'])
def get_order_payment_details(order_id):
    """
    Retrieve order total, payment method, and payment status.
    
    :param order_id: Order ID
    :return: JSON response with payment details
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        payment = Payment.query.filter_by(order_id=order_id).first()
        if payment is None:
            return jsonify({'error': 'Payment not found'}), 404
        return jsonify({'order_total': order.total_cost, 'payment_method': payment.payment_method, 'payment_status': payment.payment_status}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/confirmation-number', methods=['GET'])
def get_order_confirmation_number(order_id):
    """
    Retrieve unique order confirmation number.
    
    :param order_id: Order ID
    :return: JSON response with confirmation number
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify({'confirmation_number': 'CONF-' + str(order_id)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/receipt', methods=['GET'])
def generate_receipt(order_id):
    """
    Generate receipt for the order.
    
    :param order_id: Order ID
    :return: JSON response with receipt
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        cake = Cake.query.get(order.cake_id)
        receipt = 'Order ID: ' + str(order.id) + '\n'
        receipt += 'Cake Type: ' + cake.cake_type + '\n'
        receipt += 'Flavor: ' + cake.flavor + '\n'
        receipt += 'Design: ' + cake.design + '\n'
        receipt += 'Message: ' + cake.message + '\n'
        receipt += 'Pickup or Delivery: ' + order.pickup_or_delivery + '\n'
        receipt += 'Pickup Time: ' + order.pickup_time.strftime('%Y-%m-%d %H:%M:%S') + '\n'
        receipt += 'Delivery Address: ' + order.delivery_address + '\n'
        receipt += 'Quantity: ' + str(order.quantity) + '\n'
        receipt += 'Total Cost: ' + str(order.total_cost) + '\n'
        return jsonify({'receipt': receipt}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_order_history():
    """
    Retrieve user's order history with order details.
    
    :return: JSON response with order history
    """
    try:
        orders = Order.query.all()
        order_history = []
        for order in orders:
            cake = Cake.query.get(order.cake_id)
            order_history.append({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost})
        return jsonify({'orders': order_history}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/search', methods=['GET'])
def search_orders():
    """
    Search orders by date, order status, or cake type.
    
    :return: JSON response with search results
    """
    try:
        data = request.get_json()
        orders = Order.query.all()
        search_results = []
        for order in orders:
            cake = Cake.query.get(order.cake_id)
            if data.get('date') and order.pickup_time.strftime('%Y-%m-%d') != data['date']:
                continue
            if data.get('order_status') and order.pickup_or_delivery != data['order_status']:
                continue
            if data.get('cake_type') and cake.cake_type != data['cake_type']:
                continue
            search_results.append({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost})
        return jsonify({'orders': search_results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/reorder', methods=['POST'])
def reorder_cake(order_id):
    """
    Re-order a previous cake.
    
    :param order_id: Order ID
    :return: JSON response with new order details
    """
    try:
        order = Order.query.get(order_id)
        if order is None:
            return jsonify({'error': 'Order not found'}), 404
        cake = Cake.query.get(order.cake_id)
        new_order = Order(cake_id=cake.id, pickup_or_delivery=order.pickup_or_delivery, pickup_time=order.pickup_time, delivery_address=order.delivery_address, quantity=order.quantity, total_cost=order.total_cost)
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'order_id': new_order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': new_order.pickup_or_delivery, 'pickup_time': new_order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': new_order.delivery_address, 'quantity': new_order.quantity, 'total_cost': new_order.total_cost}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/recent', methods=['GET'])
def get_recent_orders():
    """
    Retrieve a summary of user's recent orders.
    
    :return: JSON response with recent orders
    """
    try:
        orders = Order.query.all()
        recent_orders = []
        for order in orders:
            cake = Cake.query.get(order.cake_id)
            recent_orders.append({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost})
        return jsonify({'recent_orders': recent_orders}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/filter', methods=['GET'])
def filter_orders():
    """
    Filter orders by date range or order status.
    
    :return: JSON response with filtered orders
    """
    try:
        data = request.get_json()
        orders = Order.query.all()
        filtered_orders = []
        for order in orders:
            cake = Cake.query.get(order.cake_id)
            if data.get('date_range') and order.pickup_time.strftime('%Y-%m-%d') not in data['date_range']:
                continue
            if data.get('order_status') and order.pickup_or_delivery != data['order_status']:
                continue
            filtered_orders.append({'order_id': order.id, 'cake_details': {'cake_type': cake.cake_type, 'flavor': cake.flavor, 'design': cake.design, 'message': cake.message}, 'pickup_or_delivery': order.pickup_or_delivery, 'pickup_time': order.pickup_time.strftime('%Y-%m-%d %H:%M:%S'), 'delivery_address': order.delivery_address, 'quantity': order.quantity, 'total_cost': order.total_cost})
        return jsonify({'orders': filtered_orders}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    db.create_all()
    app.run(debug=True)
