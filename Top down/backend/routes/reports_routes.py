
# Models (if needed)
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from datetime import datetime
import logging

db = SQLAlchemy()

class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    flavor = db.Column(db.String(100), nullable=False)
    design = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    sales = db.relationship('Sale', backref='cake', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cake_id = db.Column(db.Integer, db.ForeignKey('cake.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100), nullable=False)

# Routes
from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, DataError
from marshmallow import Schema, fields, validates, ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

class SalesReportSchema(Schema):
    date_range = fields.String()
    cake_type = fields.String()

class InventoryReportSchema(Schema):
    ingredient = fields.String()
    supplier = fields.String()

# Helper functions
def get_sales_report(date_range=None, cake_type=None):
    sales_report = {
        'total_sales': 0,
        'sales_by_cake_type': [],
        'sales_by_date': []
    }
    sales = Sale.query.all()
    if date_range:
        start_date, end_date = date_range.split(' - ')
        sales = [sale for sale in sales if start_date <= sale.date.strftime('%Y-%m-%d') <= end_date]
    if cake_type:
        sales = [sale for sale in sales if sale.cake.type == cake_type]
    sales_report['total_sales'] = sum(sale.total_price for sale in sales)
    for cake_type in set(sale.cake.type for sale in sales):
        sales_by_cake_type = sum(sale.total_price for sale in sales if sale.cake.type == cake_type)
        sales_report['sales_by_cake_type'].append({'cake_type': cake_type, 'sales': sales_by_cake_type})
    for date in set(sale.date.strftime('%Y-%m-%d') for sale in sales):
        sales_by_date = sum(sale.total_price for sale in sales if sale.date.strftime('%Y-%m-%d') == date)
        sales_report['sales_by_date'].append({'date': date, 'sales': sales_by_date})
    return sales_report

def get_inventory_report(ingredient=None, supplier=None):
    inventory_report = {
        'total_inventory': 0,
        'inventory_by_ingredient': [],
        'inventory_by_supplier': []
    }
    ingredients = Ingredient.query.all()
    if ingredient:
        ingredients = [ingredient for ingredient in ingredients if ingredient.name == ingredient]
    if supplier:
        ingredients = [ingredient for ingredient in ingredients if ingredient.supplier == supplier]
    inventory_report['total_inventory'] = sum(ingredient.quantity for ingredient in ingredients)
    for ingredient_name in set(ingredient.name for ingredient in ingredients):
        quantity = sum(ingredient.quantity for ingredient in ingredients if ingredient.name == ingredient_name)
        inventory_report['inventory_by_ingredient'].append({'ingredient': ingredient_name, 'quantity': quantity})
    for supplier_name in set(ingredient.supplier for ingredient in ingredients):
        quantity = sum(ingredient.quantity for ingredient in ingredients if ingredient.supplier == supplier_name)
        inventory_report['inventory_by_supplier'].append({'supplier': supplier_name, 'quantity': quantity})
    return inventory_report

# Routes
@app.route('/api/reports/sales', methods=['GET'])
@jwt_required
def generate_sales_report():
    """
    Generate a report on cake sales.

    Query Parameters:
        date_range (string): Date range in the format YYYY-MM-DD - YYYY-MM-DD
        cake_type (string): Type of cake

    Returns:
        JSON object with sales report data
    """
    try:
        schema = SalesReportSchema()
        data = request.args
        errors = schema.validate(data)
        if errors:
            return jsonify({'error': 'Invalid request parameters'}), 400
        date_range = data.get('date_range')
        cake_type = data.get('cake_type')
        sales_report = get_sales_report(date_range, cake_type)
        return jsonify(sales_report), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reports/inventory', methods=['GET'])
@jwt_required
def generate_inventory_report():
    """
    Generate a report on inventory levels.

    Query Parameters:
        ingredient (string): Name of ingredient
        supplier (string): Name of supplier

    Returns:
        JSON object with inventory report data
    """
    try:
        schema = InventoryReportSchema()
        data = request.args
        errors = schema.validate(data)
        if errors:
            return jsonify({'error': 'Invalid request parameters'}), 400
        ingredient = data.get('ingredient')
        supplier = data.get('supplier')
        inventory_report = get_inventory_report(ingredient, supplier)
        return jsonify(inventory_report), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
