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
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.order_supplier_model import OrderSupplier
from sqlalchemy.sql import exists, func, text
from app.models.account_model import Account
from app.models.client_account_model import ClientAccount
from datetime import date
from random import randint
from datetime import date, timedelta
from calendar import monthrange

@bp.route('/purchases')
def get_purchases():
    purchases = Purchase.query.all()
    items = [item.to_dict() for item in purchases]
    return jsonify(items)

@bp.route('/purchase/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)

    purchase_orders = purchase.orders_supplier.all()
    for order in purchase_orders:
        order_product_qt = order.quantity
        order_product  = Product.query.get_or_404(order.product_id)
        if(order_product.store_qt < order_product_qt):
            return bad_request(f"Cannot delete purchase. Product {order_product.part_number} has no quantity or no quantity in store")
        order_product.store_qt = order_product.store_qt - order_product_qt
        db.session.add(order_product)
        db.session.delete(order)

    # purchase_supplier = purchase.supplier
    # purchase_total_price = purchase.total_price
    # purchase_total_paid = purchase.paid

    # purchase_supplier.supplier_balance = purchase_supplier.supplier_balance - float(purchase_total_paid)
    # purchase_supplier.amount_to_get_paid = purchase_supplier.amount_to_get_paid - (float(purchase_total_price) - float(purchase_total_paid))

    # db.session.add(purchase_supplier)

    db.session.delete(purchase)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/purchases/pagination/<int:per_page>', methods=['POST'])
def get_purchases_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']
    purchases = Purchase.query.filter(Purchase.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Purchase.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    purchases = purchases.filter(Purchase.supplier.has(Client.name.contains(keyword)))

    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.asc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.asc())
            elif(sorted_field == 'supplier'):
                purchases = purchases.order_by(Purchase.supplier_id.asc())
            elif(sorted_field == 'total_price'):
                purchases = purchases.order_by(Purchase.total_price.asc())
            elif(sorted_field == 'paid'):
                purchases = purchases.order_by(Purchase.paid.asc())
        else:
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.desc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.desc())
            elif(sorted_field == 'supplier'):
                purchases = purchases.order_by(Purchase.supplier_id.desc())
            elif(sorted_field == 'total_price'):
                purchases = purchases.order_by(Purchase.total_price.desc())
            elif(sorted_field == 'paid'):
                purchases = purchases.order_by(Purchase.paid.desc())
    else:
        purchases = purchases.order_by(Purchase.id.asc())

    purchases_with_pag = purchases.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in purchases_with_pag.items]
    return jsonify({'data':items, 'total':  purchases_with_pag.total})

@bp.route('/purchase/create/<int:supp_id>', methods=['POST'])
def add_purchase(supp_id):
    data = request.get_json() or {}

    if 'paid' not in data or 'orders' not in data or 'total_price' not in data or 'taxes_included' not in data:
        return bad_request('Incomplete Info')

    paid = float(data['paid'])
    orders = data['orders']
    total_price = float(data['total_price'])
    taxes_included = True if int(data['taxes_included']) == 1 else False
    id = randint(1000000, 9999999) 
    if 'id' in data and data['id'] and data['id']:
        id = int(data['id'])

    supplier = Client.query.get_or_404(supp_id)

    representative_name = data['representative_name'].strip() if data['representative_name'] else None
    representative_number = data['representative_number'].strip() if data['representative_number'] else None
    representative_email = data['representative_email'].strip() if data['representative_email'] else None

    purchase  = None
    purchase = Purchase(id = id, paid = float(paid), total_price = total_price, supplier = supplier, taxes_included = taxes_included, representative_name=representative_name, representative_number=representative_number, representative_email = representative_email)

    for o in orders:
        product_id = int(o['product_id'])
        prod = Product.query.get_or_404(product_id)
        order = OrderSupplier(quantity = int(o['quantity']), price_per_item = float(o['price_per_item']), product= prod , supplier = supplier)
        purchase.orders_supplier.append(order)
        prod.store_qt = prod.store_qt + int(o['quantity'])
        db.session.add(prod)
        db.session.add(order)


    # supplier.supplier_balance = supplier.supplier_balance + float(paid)
    # supplier.amount_to_get_paid = supplier.amount_to_get_paid + (float(total_price) - float(paid))

    db.session.add(supplier)
    db.session.add(purchase)
    db.session.commit()
    return jsonify(purchase.to_dict())



