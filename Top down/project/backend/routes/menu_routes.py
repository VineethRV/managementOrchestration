
# Models (if needed)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# Define many-to-many relationship between Menu and Role
menu_role = Table('menu_role', db.Model.metadata,
    Column('menu_id', Integer, ForeignKey('menu.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class Menu(db.Model):
    """Navigation menu item model"""
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(100), nullable=False)
    icon = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('menu.id'))
    order = Column(Integer, nullable=False)
    roles = relationship('Role', secondary=menu_role, backref=db.backref('menus', lazy=True))

    def __repr__(self):
        return f"Menu('{self.name}', '{self.url}')"

class Role(db.Model):
    """Role model"""
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"Role('{self.name}')"

# Routes
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, DataError
import logging

menu_blueprint = Blueprint('menu', __name__)

@menu_blueprint.route('/api/menu/items', methods=['GET'])
@jwt_required()
def get_navigation_menu():
    """
    Retrieve navigation menu items.

    Returns:
        JSON array of navigation menu items.
    """
    try:
        # Get user role from JWT token
        user_role = get_jwt_identity()

        # Query menu items for the user's role
        menu_items = Menu.query.join(menu_role).join(Role).filter(Role.name == user_role).all()

        # Serialize menu items to JSON
        menu_items_json = []
        for item in menu_items:
            menu_items_json.append({
                'id': item.id,
                'name': item.name,
                'url': item.url,
                'icon': item.icon,
                'roles': [role.name for role in item.roles],
                'parentId': item.parent_id,
                'order': item.order
            })

        return jsonify(menu_items_json), 200

    except Exception as e:
        logging.error(f"Error retrieving menu items: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Helper functions if needed
def get_user_role(token):
    # Implement logic to get user role from JWT token
    pass
