from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.sale_model import Sale
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.order_customer_model import OrderCustomer
from sqlalchemy.sql import exists, func
from app.models.account_model import Account
from app.models.client_account_model import ClientAccount
from datetime import date

@bp.route('/sales')
def get_sales():
    sales = Sale.query.all()
    items = [item.to_dict() for item in sales]
    return jsonify(items)

@bp.route('/sales/pagination/<int:per_page>')
def get_sales_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']
    sale_type = int(request.args['saletype']) if request.args['saletype'] else None
    sales = Sale.query
    if(sale_type == 1):
        sales = Sale.query.filter(Sale.sale_type == True)
    elif(sale_type == 0):
        sales = Sale.query.filter(Sale.sale_type == False)

    sales = sales.filter(Sale.customer.has(Client.name.contains(keyword)))

    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.asc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.asc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.asc())

        else:
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.desc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.desc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.desc())
    else:
        sales = sales.order_by(Sale.id.asc())

    sales_with_pag = sales.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in sales_with_pag.items]
    return jsonify({'data':items, 'total':  sales_with_pag.total})


@bp.route('/sale/create/<int:cust_id>', methods=['POST'])
def add_sale(cust_id):
    data = request.get_json() or {}

    if 'paid' not in data or 'orders' not in data or 'total_price' not in data or 'taxes_add' not in data or 'reduction_add' not in data or 'official' not in data:
        return bad_request('Incomplete Info')

    paid = float(data['paid'])
    orders = data['orders']
    total_price = float(data['total_price'])
    official = int(data['official'])
    taxes_add = True if int(data['taxes_add']) == 1 else False
    reduction_add = True if int(data['reduction_add']) == 1 else False

    representative_name = data['representative_name'].strip() if data['representative_name'] else None
    representative_number = data['representative_number'].strip() if data['representative_number'] else None

    customer = Client.query.get_or_404(cust_id)
    
    sale  = None
    if(official):
        official = True
        lastSale = Sale.query.filter(Sale.sale_type == True).order_by(Sale.id.desc()).limit(1).first()
        if(lastSale is None):
            sale =  Sale(taxes_add=taxes_add, reduction_add = reduction_add, paid =float(paid), total_price = total_price, customer = customer, sale_type = official, representative_name=representative_name, representative_number=representative_number, unofficial_id=None)
        else:
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid =float(paid), total_price = total_price, customer = customer, sale_type = official, official_id = lastSale.official_id+1, representative_name=representative_name, representative_number=representative_number, unofficial_id=None)

    else:
        official = False
        lastSale = Sale.query.filter(Sale.sale_type == False).order_by(Sale.id.desc()).limit(1).first()
        if(lastSale is None):
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid =float(paid), total_price = total_price, customer = customer, sale_type = official, representative_name=representative_name, representative_number=representative_number, official_id=None)
        else:
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid =float(paid), total_price = total_price, customer = customer, sale_type = official, unofficial_id = lastSale.unofficial_id+1, representative_name=representative_name, representative_number=representative_number,official_id=None)
   
    for o in orders:
        product_id = int(o['product_id'])
        prod = Product.query.get_or_404(product_id)
        if(prod.store_qt < int(o['quantity'])):
            return bad_request("Product {} doesn\'t have enough quantity in store".format(prod.part_number))
        order = OrderCustomer(quantity = int(o['quantity']), price_per_item = float(o['price_per_item']), product= prod , customer = customer)
        sale.orders_customer.append(order)
        prod.store_qt = prod.store_qt - int(o['quantity'])
        db.session.add(prod)
        db.session.add(order)

    customer.customer_balance = customer.customer_balance + float(paid)
    customer.amount_to_pay = customer.amount_to_pay + (float(total_price) - float(paid))

    db.session.add(customer)
    db.session.add(sale)
    db.session.commit()
    return jsonify(sale.to_dict())