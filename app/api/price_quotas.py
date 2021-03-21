from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.price_quotas_model import PriceQuotas
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.order_price_quota_model import OrderPriceQuota
from sqlalchemy.sql import exists, func, text
from app.models.account_model import Account
from app.models.client_account_model import ClientAccount
from datetime import date, timedelta
from calendar import monthrange
import pandas as pd
from app.models.employee_model import Employee

@bp.route('/pricequotas')
def get_pricequotas():
    price_quotas = PriceQuotas.query.all()
    items = [item.to_dict() for item in price_quotas]
    return jsonify(items)

@bp.route('/pricequota/<int:id>', methods=['DELETE'])
def delete_pricequotas(id):
    pricequota = PriceQuotas.query.get_or_404(id)

    orders = pricequota.orders_customer.all()
    for order in orders:
        db.session.delete(order)

    db.session.delete(pricequota)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/pricequotas/pagination/<int:per_page>', methods=['POST'])
def get_pricequotas_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']
    # print(filters)

    pricequotas = PriceQuotas.query.filter(PriceQuotas.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(PriceQuotas.date <= '{}-{:02d}-{:02d}'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    pricequotas = pricequotas.filter(PriceQuotas.customer.has(Client.name.contains(keyword)))

    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                pricequotas = pricequotas.order_by(PriceQuotas.id.asc())
            elif(sorted_field == 'date'):
                pricequotas = pricequotas.order_by(PriceQuotas.date.asc())
            elif(sorted_field == 'customer'):
                pricequotas = pricequotas.order_by(PriceQuotas.customer_id.asc())
            elif(sorted_field == 'total_price'):
                pricequotas = pricequotas.order_by(PriceQuotas.total_price.asc())
        else:
            if(sorted_field == 'id'):
                pricequotas = pricequotas.order_by(PriceQuotas.id.desc())
            elif(sorted_field == 'date'):
                pricequotas = pricequotas.order_by(PriceQuotas.date.desc())
            elif(sorted_field == 'customer'):
                pricequotas = pricequotas.order_by(PriceQuotas.customer_id.desc())
            elif(sorted_field == 'total_price'):
                pricequotas = pricequotas.order_by(PriceQuotas.total_price.desc())
    else:
        pricequotas = pricequotas.order_by(PriceQuotas.id.asc())

    pricequotas_with_pag = pricequotas.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in pricequotas_with_pag.items]
    return jsonify({'data':items, 'total':  pricequotas_with_pag.total})



@bp.route('/pricequotas/create/<int:cust_id>', methods=['POST'])
def add_pricequotas(cust_id):
    data = request.get_json() or {}

    if 'orders' not in data or 'total_price' not in data:
        return bad_request('Incomplete Info')

    orders = data['orders']
    total_price = float(data['total_price'])

    representative_name = data['representative_name'].strip() if data['representative_name'] else None
    representative_number = data['representative_number'].strip() if data['representative_number'] else None
    representative_email = data['representative_email'].strip() if data['representative_email'] else None
    # employees = data['employees']

    customer = Client.query.get_or_404(cust_id)
    
    pricequotas =  PriceQuotas(total_price = total_price, customer = customer, representative_name=representative_name, representative_number=representative_number, representative_email = representative_email)

    for o in orders:
        product_id = int(o['product_id'])
        prod = Product.query.get_or_404(product_id)
        order = OrderPriceQuota(quantity = int(o['quantity']), price_per_item = float(o['price_per_item']), product= prod , customer = customer)
        pricequotas.orders_customer.append(order)
        db.session.add(prod)
        db.session.add(order)

    # for emp_id in employees:
    #     employee = Employee.query.get_or_404(emp_id)
    #     sale.employees.append(employee)
    #     db.session.add(employee)

    db.session.add(customer)
    db.session.add(pricequotas)
    db.session.commit()
    return jsonify(pricequotas.to_dict())

