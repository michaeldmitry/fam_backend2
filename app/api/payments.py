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
from app.models.payment_supplier_model import PaymentSupplier
from app.models.payment_customer_model import PaymentCustomer
from app.models.account_model import Account
from app.models.client_account_model import ClientAccount
from datetime import date

@bp.route('/payments/supplier', methods=['GET'])
def get_supps_payments():
    payments = PaymentSupplier.query.all()
    items = [item.to_dict() for item in payments]
    return jsonify(items)

@bp.route('/payments/supplier/pagination/<int:per_page>')
def get_suppliers_payments_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    supplier_payments = PaymentSupplier.query.filter(PaymentSupplier.supplier.has(Client.name.contains(keyword)))

    if(sorted_field != "" and order != ""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.id.asc())
            elif(sorted_field == 'date'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.date.asc())
            elif(sorted_field == 'supplier'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.supplier_id.asc())
        else:
            if(sorted_field == 'id'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.id.desc())
            elif(sorted_field == 'date'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.date.desc())
            elif(sorted_field == 'supplier'):
                supplier_payments = supplier_payments.order_by(PaymentSupplier.supplier_id.desc())
    else:
        supplier_payments = supplier_payments.order_by(PaymentSupplier.id.asc())

    supplier_payments_with_pag = supplier_payments.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in supplier_payments_with_pag.items]
    return jsonify({'data':items, 'total':  supplier_payments_with_pag.total})

@bp.route('/payments/supplier/create/<int:supp_id>', methods=['POST'])
def add_supp_payments(supp_id):
    data = request.get_json() or {}

    supplier = Client.query.get_or_404(supp_id)
    if('amount' not in data):
        return bad_request('Must include amount')

    payment = PaymentSupplier(amount = float(data['amount']), supplier = supplier)

    rest = supplier.amount_to_get_paid - float(data['amount'])
    balance_add = 0
    outstanding_add = 0

    if(rest>= 0):
        supplier.amount_to_get_paid = supplier.amount_to_get_paid - float(data['amount'])
        supplier.supplier_balance = supplier.supplier_balance+ (float(data['amount']))
    else:
        supplier.amount_to_get_paid = 0
        supplier.supplier_balance = supplier.supplier_balance + abs(rest)

    db.session.add(supplier)
    db.session.add(payment)
    db.session.commit()

    return jsonify(payment.to_dict())
    
@bp.route('/payments/customer/pagination/<int:per_page>')
def get_customers_payments_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    customer_payments = PaymentCustomer.query.filter(PaymentCustomer.customer.has(Client.name.contains(keyword)))

    if(sorted_field != "" and order != ""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                customer_payments = customer_payments.order_by(PaymentCustomer.id.asc())
            elif(sorted_field == 'date'):
                customer_payments = customer_payments.order_by(PaymentCustomer.date.asc())
            elif(sorted_field == 'customer'):
                customer_payments = customer_payments.order_by(PaymentCustomer.customer_id.asc())
        else:
            if(sorted_field == 'id'):
                customer_payments = customer_payments.order_by(PaymentCustomer.id.desc())
            elif(sorted_field == 'date'):
                customer_payments = customer_payments.order_by(PaymentCustomer.date.desc())
            elif(sorted_field == 'customer'):
                customer_payments = customer_payments.order_by(PaymentCustomer.customer_id.desc())
    else:
        customer_payments = customer_payments.order_by(PaymentCustomer.id.asc())

    customer_payments_with_pag = customer_payments.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in customer_payments_with_pag.items]
    return jsonify({'data':items, 'total':  customer_payments_with_pag.total})

@bp.route('/payments/customer/create/<int:cust_id>', methods=['POST'])
def add_cust_payments(cust_id):
    data = request.get_json() or {}

    customer = Client.query.get_or_404(cust_id)
    if('amount' not in data):
        return bad_request('Must include amount')

    payment = PaymentCustomer(amount = float(data['amount']), customer = customer)

    rest = customer.amount_to_pay - float(data['amount'])
    balance_add = 0
    outstanding_add = 0

    if(rest>= 0):
        customer.amount_to_pay = customer.amount_to_pay - float(data['amount'])
        customer.customer_balance = customer.customer_balance+ (float(data['amount']))
    else:
        customer.amount_to_pay = 0
        customer.customer_balance = customer.customer_balance + abs(rest)

    db.session.add(customer)
    db.session.add(payment)
    db.session.commit()

    return jsonify(payment.to_dict())