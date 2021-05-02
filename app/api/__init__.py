from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import clients, products, warehouses, purchases, payments, orders, reallocations, categories, brands, subcategories, sales, general, employees, price_quotas, users, auth, sale_drafts