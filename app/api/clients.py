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
from sqlalchemy import text

@bp.route('/supplier/create', methods= ['POST'])
def create_supplier():
    data = request.get_json() or {}
    if 'name' not in data or 'email' not in data or 'phone_number' not in data or'address' not in data:
        return bad_request('Incomplete supplier info')

    if Client.query.filter_by(name=data["name"]).first():
        return bad_request('Client name already exists')

    data['name'] = data['name'].strip()
    data['email'] = data['email'].strip()
    data['phone_number'] = data['phone_number'].strip()
    data['address'] = data['address'].strip()

    user = Client(name = data['name'], role="supplier", email=data['email'], phone_number=data['phone_number'], address=data['address'])
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict(role = "supplier"))
    response.status_code = 201
    return response

@bp.route('/suppliers')
def get_suppliers():
    data = Client.query.filter(Client.role == "supplier").all()
    items = [item.to_dict(role = "supplier") for item in data]
    return jsonify(items)



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
    # print(Client.__table__.columns)

    supliers = Client.query.filter(Client.role== "supplier", Client.name.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.asc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.asc())

        else:
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.desc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.desc())
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



@bp.route('/suppliers/purchases/pagination/<int:supp_id>/<int:per_page>')
def get_supplier_purchases_with_pag(supp_id,per_page):
    curr_page = int(request.args['current'])
    # keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    supplier = Client.query.get_or_404(supp_id)
    purchases = supplier.supplier_purchases
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.asc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.asc())

        else:
            if(sorted_field == 'id'):
                purchases = purchases.order_by(Purchase.id.desc())
            elif(sorted_field == 'date'):
                purchases = purchases.order_by(Purchase.date.desc())
    else:
        purchases = purchases.order_by(Purchase.id.asc())

    purchases_with_pag = purchases.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in purchases_with_pag.items]
    return jsonify({'data':items, 'total': purchases_with_pag.total})


@bp.route('/suppliers/payments/pagination/<int:supp_id>/<int:per_page>')
def get_supplier_payments_with_pag(supp_id,per_page):
    curr_page = int(request.args['current'])
    # keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    supplier = Client.query.get_or_404(supp_id)
    payments = supplier.supplier_payments
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentSupplier.id.asc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentSupplier.date.asc())

        else:
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentSupplier.id.desc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentSupplier.date.desc())
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

@bp.route('/supplier/activity/pagination/<int:supp_id>/<int:per_page>')
def get_supplier_activity_with_pag(supp_id,per_page):
    curr_page = int(request.args['current'])
    # keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']
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

    activity = supplier.getActivityQuery(role="supplier", field = field_param, order = order_param, page_no = curr_page, rows_per_page = per_page)
    if(activity is None):
        return bad_request('Something wrong happened from our side')

    res = [dict(row) for row in activity]
  
    return jsonify({'data':res, 'total': res[0]['Total_count']})

@bp.route('/supplier/activity/<int:supp_id>')
def get_supp_activity(supp_id):
    supplier = Client.query.get_or_404(supp_id)
    activity = supplier.getActivity(role = "supplier")
    return jsonify(activity)


@bp.route('/customer/create', methods= ['POST'])
def create_customer():
    data = request.get_json() or {}
    if 'name' not in data or 'email' not in data or 'phone_number' not in data or 'address' not in data:
        return bad_request('Incomplete Info')

    data['name'] = data['name'].strip()

    if Client.query.filter_by(name=data["name"]).first():
        return bad_request('Customer name already exists')

    data['email'] = data['email'].strip()
    data['phone_number'] = data['phone_number'].strip()
    data['address'] = data['address'].strip()
    
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