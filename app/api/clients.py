from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.client_model import Client
from app.models.purchase_model import Purchase
from app.models.payment_supplier_model import PaymentSupplier
from sqlalchemy import asc, desc
from sqlalchemy import text, func
from app.models.category_model import Category
from datetime import date, timedelta
from calendar import monthrange

@bp.route('/suppliers/owed')
def get_owed_money():
    total = Client.query.with_entities(func.sum(Client.amount_to_get_paid).label("total")).filter_by(role ="supplier").first()
    return jsonify({'total': total.total})


@bp.route('/supplier/create', methods= ['POST'])
def create_supplier():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('Incomplete supplier info')

    if Client.query.filter_by(name=data["name"]).first():
        return bad_request('Client name already exists')

    data['name'] = data['name'].strip()
    data['email'] = data['email'].strip() if data['email'] else None
    data['phone_number'] = data['phone_number'].strip() if data['phone_number'] else None
    data['address'] = data['address'].strip() if data['address'] else None
    categories = data['categories']

    user = Client(name = data['name'], role="supplier", email=data['email'], phone_number=data['phone_number'], address=data['address'])

    for cat_id in categories:
        category = Category.query.get_or_404(cat_id)
        user.categories.append(category)
        db.session.add(category)


    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict(role = "supplier"))
    response.status_code = 201
    return response

@bp.route('/suppliers')
def get_suppliers():
    data = Client.query.filter(Client.role == "supplier").all()
    items = [item.to_dict(role = "supplier", extraInfo=True) for item in data]
    return jsonify(items)

@bp.route('/supplier/<int:user_id>', methods=['PUT'])
def update_supplier(user_id):
    data = request.get_json() or {}
    supplier = Client.query.get_or_404(user_id)
    data['name'] = data['name'].strip() if data['name'] else None
    data['address'] = data['address'].strip() if data['address'] else None
    data['phone_number'] = data['phone_number'].strip() if data['phone_number'] else None
    data['email']= data['email'].strip() if data['email'] else None

    if (Client.query.filter(Client.name == data['name'], Client.id != user_id).first() is not None):
        return bad_request('There is already a supplier with the same name')


    supplier.from_dict(data)

    db.session.add(supplier)
    db.session.commit()
    
    return jsonify(supplier.to_dict(role="supplier"))

@bp.route('/supplier/<int:user_id>', methods=['DELETE'])
def delete_supplier(user_id):
    supplier = Client.query.get_or_404(user_id)

    if (supplier.supplier_purchases.first() is not None or supplier.supplier_payments.first() is not None):
        return bad_request('Already had activity with this supplier')

    supplier.categories= []
    db.session.commit()

    db.session.delete(supplier)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/suppliers/pages/<int:per_page>')
def get_suppliers_pages_no(per_page):
    supliers = Client.query.filter(Client.role== "supplier").order_by(Client.id.asc())
    suppliers_with_pag = supliers.paginate(per_page = per_page,  error_out=True)
    return jsonify({'pages': suppliers_with_pag.pages})

@bp.route('/suppliers/pagination/<int:per_page>')
def get_suppliers_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']
    cat = int(request.args['cat'])

    supliers = Client.query
    if(cat != -1):
        supliers = supliers.filter(Client.categories.any(Category.id == cat))

    supliers = supliers.filter(Client.role== "supplier", Client.name.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.asc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.asc())
            elif(sorted_field == 'amount_to_get_paid'):
                supliers = supliers.order_by(Client.amount_to_get_paid.asc())

        else:
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.desc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.desc())
            elif(sorted_field == 'amount_to_get_paid'):
                supliers = supliers.order_by(Client.amount_to_get_paid.desc())
    else:
        supliers = supliers.order_by(Client.id.asc())

    suppliers_with_pag = supliers.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict(role = "supplier") for item in suppliers_with_pag.items]
    return jsonify({'data':items, 'total':  suppliers_with_pag.total})

@bp.route('/supplier/<int:supp_id>')
def get_supplier(supp_id):
    supplier = Client.query.get_or_404(supp_id)
    return jsonify(supplier.to_dict(role="supplier", extraInfo=True))


@bp.route('/supplier/purchases/<int:supp_id>')
def get_supp_purchases(supp_id):
    supplier = Client.query.get_or_404(supp_id)
    purchases  = supplier.supplier_purchases.all()
    items = [item.to_dict() for item in purchases]
    return jsonify(items)



@bp.route('/suppliers/purchases/pagination/<int:supp_id>/<int:per_page>', methods=['POST'])
def get_supplier_purchases_with_pag(supp_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    supplier = Client.query.get_or_404(supp_id)
    purchases = supplier.supplier_purchases
    purchases = purchases.filter(Purchase.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Purchase.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.asc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.asc())
            elif(sorted_field == 'paid'):
                purchases = purchases.order_by(Purchase.paid.asc())
            elif(sorted_field == 'total_price'):
                purchases = purchases.order_by(Purchase.total_price.asc())
            

        else:
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.desc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.desc())
            elif(sorted_field == 'paid'):
                purchases = purchases.order_by(Purchase.paid.desc())
            elif(sorted_field == 'total_price'):
                purchases = purchases.order_by(Purchase.total_price.desc())
    else:
        purchases = purchases.order_by(Purchase.id.asc())

    purchases_with_pag = purchases.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in purchases_with_pag.items]
    return jsonify({'data':items, 'total': purchases_with_pag.total})


@bp.route('/supplier/accumulated/<int:supp_id>', methods=['GET'])
def get_supplier_accumulated(supp_id):
    min_month = int(request.args['min_month'])
    min_year = int(request.args['min_year'])

    result = db.engine.execute(text("select sum(paid) as total_paid, sum(total_price) as total_price from ( select purchase.id, purchase.date, purchase.paid, purchase.total_price, purchase.supplier_id from purchase where purchase.supplier_id = {} \
                                    and DATE(purchase.date) < '{}-{}-01' union all select payment_supplier.id,  payment_supplier.date,\
                                    payment_supplier.amount, Null as col5, payment_supplier.supplier_id from payment_supplier\
                                    where payment_supplier.supplier_id={} and DATE(payment_supplier.date) < '{}-{}-01') x group by supplier_id;".format(supp_id, min_year, min_month, supp_id, min_year, min_month)))
    res = [dict(row) for row in result]
    if(len(res) > 0):
        return jsonify(res[0])
    else:
        return jsonify({"total_paid": 0, "total_price": 0})

@bp.route('/dates/supplier/activity/<int:supp_id>', methods=['GET'])
def get_dates_range_supplier_activity(supp_id):
    result = db.engine.execute(text("select min(min_year) as min_year, max(max_year) as max_year FROM (select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from purchase where supplier_id = {} UNION SELECT min(YEAR(date)) as min_year, max(YEAR(DATE)) as max_year from payment_supplier where supplier_id={}) s".format(supp_id, supp_id)))
    res = [dict(row) for row in result]
    if(len(res) > 0):
        return jsonify(res[0])
    else:
        return jsonify({"min_year": "", "max_year": ""})

@bp.route('/suppliers/payments/pagination/<int:supp_id>/<int:per_page>', methods=['POST'])
def get_supplier_payments_with_pag(supp_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    supplier = Client.query.get_or_404(supp_id)
    payments = supplier.supplier_payments
    payments = payments.filter(PaymentSupplier.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(PaymentSupplier.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentSupplier.id.asc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentSupplier.date.asc())
            elif(sorted_field == 'amount'):
                payments = payments.order_by(PaymentSupplier.amount.asc())

        else:
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentSupplier.id.desc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentSupplier.date.desc())
            elif(sorted_field == 'amount'):
                payments = payments.order_by(PaymentSupplier.amount.desc())
    else:
        payments = payments.order_by(PaymentSupplier.id.asc())

    payments_with_pag = payments.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in payments_with_pag.items]
    return jsonify({'data':items, 'total': payments_with_pag.total})


@bp.route('/supplier/payments/<int:supp_id>')
def get_supp_payments(supp_id):
    supplier = Client.query.get_or_404(supp_id)
    payments  = supplier.supplier_payments.all()
    items = [item.to_dict() for item in payments]
    return jsonify(items)

@bp.route('/supplier/activity/pagination/<int:supp_id>/<int:per_page>', methods=['POST'])
def get_supplier_activity_with_pag(supp_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']


    supplier = Client.query.get_or_404(supp_id)
    field_param = None
    order_param = None
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                field_param = "id"
                order_param = "ASC"
            elif(sorted_field == 'date'):
                field_param = "date"
                order_param = "ASC"
        else:
            if(sorted_field == 'id'):
                field_param = "id"
                order_param = "DESC"
            elif(sorted_field == 'date'):
                field_param = "date"
                order_param = "DESC"
    else:
        field_param = "id"
        order_param = "ASC"

    activity = supplier.getActivityQuery(role="supplier", field = field_param, order = order_param, page_no = curr_page, rows_per_page = per_page, min_month = filters['min_month'], min_year = filters['min_year'], max_month=filters['max_month'], max_year = filters['max_year'])
    if(activity is None):
        return bad_request('Something wrong happened from our side')

    res = [dict(row) for row in activity]
    return jsonify({'data':res, 'total': res[0]['Total_count'] if len(res)>0 else 0})

@bp.route('/supplier/activity/print/<int:supp_id>', methods=['POST'])
def get_supp_activity(supp_id):
    data = request.get_json() or {}
    if 'filters' not in data:
        return bad_request('Must include filters')
    filters = data['filters']

    supplier = Client.query.get_or_404(supp_id)
    activity = supplier.getActivityPrint(role = "supplier", min_month = filters['min_month'], min_year = filters['min_year'], max_month=filters['max_month'], max_year = filters['max_year'])
    if(activity is None):
        return bad_request('Something wrong happened from our side')
    res = [dict(row) for row in activity]
    return jsonify({'data':res})


@bp.route('/customer/create', methods= ['POST'])
def create_customer():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('Incomplete Info')

    data['name'] = data['name'].strip()

    if Client.query.filter_by(name=data["name"]).first():
        return bad_request('Customer name already exists')

    data['email'] = data['email'].strip() if data['email'] else None
    data['phone_number'] = data['phone_number'].strip() if data['phone_number'] else None
    data['address'] = data['address'].strip() if data['address'] else None
    
    user = Client(name = data['name'], role="customer", email = data['email'], phone_number = data['phone_number'], address = data['address'])
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict(role = "customer"))
    response.status_code = 201
    return response

@bp.route('/customers')
def get_customers():
    data = Client.query.filter(Client.role == "customer").all()
    items = [item.to_dict(role = "customer") for item in data]
    return jsonify(items)

@bp.route('/customer/<int:supp_id>')
def get_customer(cust_id):
    customer = Client.query.get_or_404(cust_id)
    return jsonify(customer.to_dict(role="customer", extraInfo=True))

@bp.route('/customers/pagination/<int:per_page>')
def get_customers_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    customers = Client.query.filter(Client.role== "customer", Client.name.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                customers = customers.order_by(Client.id.asc())
            elif(sorted_field == 'name'):
                customers = customers.order_by(Client.name.asc())

        else:
            if(sorted_field == 'id'):
                customers = customers.order_by(Client.id.desc())
            elif(sorted_field == 'name'):
                customers = customers.order_by(Client.name.desc())
    else:
        customers = customers.order_by(Client.id.asc())

    customers_with_pag = customers.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict(role = "customer") for item in customers_with_pag.items]
    return jsonify({'data':items, 'total':  customers_with_pag.total})

@bp.route('/customer/sales/<int:cust_id>')
def get_cust_sales(cust_id):
    customer = Client.query.get_or_404(cust_id)
    sales  = customer.customer_sales.all()
    items = [item.to_dict() for item in sales]
    return jsonify(items)

@bp.route('/customer/payments/<int:cust_id>')
def get_cust_payments(cust_id):
    customer = Client.query.get_or_404(cust_id)
    payments  = customer.customer_payments.all()
    items = [item.to_dict() for item in payments]
    return jsonify(items)

@bp.route('/customer/activity/<int:cust_id>')
def get_cust_activity(cust_id):
    customer = Client.query.get_or_404(cust_id)
    activity = customer.getActivity(role = "customer")
    return jsonify(activity)