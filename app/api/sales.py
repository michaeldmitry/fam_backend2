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
from sqlalchemy.sql import exists, func, text
from app.models.account_model import Account
from app.models.client_account_model import ClientAccount
from datetime import date, timedelta
from calendar import monthrange
from app.models.employee_model import Employee

@bp.route('/sales')
def get_sales():
    sales = Sale.query.all()
    items = [item.to_dict() for item in sales]
    return jsonify(items)

@bp.route('/sales/chart', methods=['GET'])
def get_sales_chart():
    min_year = int(request.args['min_year'])
    min_month = int(request.args['min_month'])
    max_year = int(request.args['max_year'])
    max_month = int(request.args['max_month'])
    sales = db.session.query(func.count(Sale.date).label('count'), Sale.date).filter(Sale.date >= '{}-{:02d}-01'.format(min_year, min_month)).filter(Sale.date <= '{}-{:02d}-{:02d} 23:59:59'.format(max_year, max_month, monthrange(max_year, max_month)[1])).group_by(func.date(Sale.date)).order_by(Sale.date)
    sales_price = db.session.query(func.round(func.sum(Sale.total_price),2).label('total'), func.count(Sale.id).label('count')).filter(Sale.date >= '{}-{:02d}-01'.format(min_year, min_month)).filter(Sale.date <= '{}-{:02d}-{:02d}'.format(max_year, max_month, monthrange(max_year, max_month)[1])).first()

    arr = [ {'x': sale.date, 'y': sale.count} for sale in sales.all()]
    return jsonify({'arr':arr, 'price': sales_price.total, 'count': sales_price.count})


@bp.route('/sales/pagination/<int:per_page>', methods=['POST'])
def get_sales_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search']
    sorted_field = data['field']
    order = data['order']
    sale_type = int(data['saletype'])
    filters = data['filters']
    # print(filters)

    sales = Sale.query.filter(Sale.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Sale.date <= '{}-{:02d}-{:02d}'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    
    if(sale_type == 1):
        sales = sales.filter(Sale.sale_type == True)
    elif(sale_type == 0):
        sales = sales.filter(Sale.sale_type == False)

    sales = sales.filter(Sale.customer.has(Client.name.contains(keyword)))

    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.asc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.asc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.asc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.asc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.asc())
        else:
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.desc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.desc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.desc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.desc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.desc())
    else:
        sales = sales.order_by(Sale.id.asc())

    sales_with_pag = sales.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in sales_with_pag.items]
    return jsonify({'data':items, 'total':  sales_with_pag.total})


@bp.route('/sale/pay/<int:sale_id>', methods=['PUT'])
def pay_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)


    data = request.get_json() or {}
    if 'paid' not in data:
        return bad_request('Incomplete Info')
    
    if sale.paid is not None:
        return bad_request('Sale has already been paid')

    data['paid'] = float(data['paid'])
    if(data['paid'] < 0 or data['paid'] > sale.total_price):
        return bad_request('Invalid Amount')

    sale.paid = data['paid']
    # customer = sale.customer
    # customer.amount_to_pay = customer.amount_to_pay - data['paid']
    # customer.customer_balance = customer.customer_balance + data['paid']
    
    db.session.add(sale)
    db.session.commit()
    return jsonify(sale.to_dict())


@bp.route('/sale/create/<int:cust_id>', methods=['POST'])
def add_sale(cust_id):
    data = request.get_json() or {}

    if 'orders' not in data or 'total_price' not in data or 'taxes_add' not in data or 'reduction_add' not in data or 'official' not in data:
        return bad_request('Incomplete Info')

    paid = float(data['paid']) if 'paid' in data and data['paid'] else None
    orders = data['orders']
    total_price = float(data['total_price'])
    official = int(data['official'])
    taxes_add = True if int(data['taxes_add']) == 1 else False
    reduction_add = True if int(data['reduction_add']) == 1 else False

    representative_name = data['representative_name'].strip() if data['representative_name'] else None
    representative_number = data['representative_number'].strip() if data['representative_number'] else None
    representative_email = data['representative_email'].strip() if data['representative_email'] else None
    employees = data['employees']

    customer = Client.query.get_or_404(cust_id)
    
    sale  = None
    if(official):
        official = True
        lastSale = Sale.query.filter(Sale.sale_type == True).order_by(Sale.id.desc()).limit(1).first()
        if(lastSale is None):
            sale =  Sale(taxes_add=taxes_add, reduction_add = reduction_add, paid = (paid), total_price = total_price, customer = customer, sale_type = official, representative_name=representative_name, representative_number=representative_number, unofficial_id=None, representative_email = representative_email)
        else:
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid = (paid), total_price = total_price, customer = customer, sale_type = official, official_id = lastSale.official_id+1, representative_name=representative_name, representative_number=representative_number, unofficial_id=None, representative_email = representative_email)

    else:
        official = False
        lastSale = Sale.query.filter(Sale.sale_type == False).order_by(Sale.id.desc()).limit(1).first()
        if(lastSale is None):
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid =(paid), total_price = total_price, customer = customer, sale_type = official, representative_name=representative_name, representative_number=representative_number, official_id=None, representative_email = representative_email)
        else:
            sale =  Sale(reduction_add = reduction_add, taxes_add=taxes_add, paid =(paid), total_price = total_price, customer = customer, sale_type = official, unofficial_id = lastSale.unofficial_id+1, representative_name=representative_name, representative_number=representative_number,official_id=None, representative_email = representative_email)
   
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

    for emp_id in employees:
        employee = Employee.query.get_or_404(emp_id)
        sale.employees.append(employee)
        db.session.add(employee)
    # if(paid):
    #     customer.customer_balance = customer.customer_balance + float(paid)
    #     customer.amount_to_pay = customer.amount_to_pay + (float(total_price) - float(paid))
    # else:
    #     customer.amount_to_pay = customer.amount_to_pay + float(total_price)

    db.session.add(customer)
    db.session.add(sale)
    db.session.commit()
    return jsonify(sale.to_dict())

