from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.purchase_model import Purchase
from app.models.sale_model import Sale
from app.models.price_quotas_model import PriceQuotas
from app.models.order_supplier_model import OrderSupplier
from app.models.order_customer_model import OrderCustomer
from app.models.order_price_quota_model import OrderPriceQuota

@bp.route('/orders/purchase/<int:purchase_id>')
def get_purchase_orders(purchase_id):
    purchase  = Purchase.query.get_or_404(purchase_id)

    orders = purchase.orders_supplier.all()
    items = [item.to_dict() for item in orders]
    return jsonify(items)

@bp.route('/orders/sale/<int:sale_id>')
def get_sale_orders(sale_id):
    sale  = Sale.query.get_or_404(sale_id)
    orders = sale.orders_customer.all()
    items = [item.to_dict() for item in orders]
    return jsonify(items)

@bp.route('/orders/pricequotas/<int:quota_id>')
def get_pricequotas_orders(quota_id):
    pricequota  = PriceQuotas.query.get_or_404(quota_id)
    orders = pricequota.orders_customer.all()
    items = [item.to_dict() for item in orders]
    return jsonify(items)