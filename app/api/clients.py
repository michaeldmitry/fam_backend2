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
from sqlalchemy import literal
from sqlalchemy import union_all
from app.models.sale_model import Sale
from app.models.payment_customer_model import PaymentCustomer

@bp.route('/suppliers/owed')
def get_owed_money():
    sql = text("SELECT ROUND(IFNULL(sum(total_price - paid),0),2) as owed FROM ((\
                select purchase.id, purchase.paid, purchase.total_price\
                from purchase)  union all \
                (select payment_supplier.id, payment_supplier.amount, 0 as col4\
                from payment_supplier)) s;")

    total_exec = db.session.execute(sql)
    res = [dict(row) for row in total_exec]
    # total = Client.query.with_entities(func.sum(Client.amount_to_get_paid).label("total")).filter_by(role ="supplier").first()
    return jsonify({'total': res[0]['owed']})

@bp.route('/customers/owed')
def get_owed_money_customers():
    sql = text("SELECT ROUND(IFNULL(sum(total_price - paid),0),2) as owed FROM ((\
                select sale.id, IFNULL(sale.paid,0) as paid, sale.total_price\
                from sale where sale.is_active = true)  union all \
                (select payment_customer.id, payment_customer.amount, 0 as col4\
                from payment_customer)) s;")

    total_exec = db.session.execute(sql)
    res = [dict(row) for row in total_exec]
    # total = Client.query.with_entities(func.sum(Client.amount_to_get_paid).label("total")).filter_by(role ="supplier").first()
    return jsonify({'total': res[0]['owed']})

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

@bp.route('/customer/<int:user_id>', methods=['PUT'])
def update_customer(user_id):
    data = request.get_json() or {}
    customer = Client.query.get_or_404(user_id)
    # print(data)
    data['name'] = data['name'].strip() if data['name'] else None
    data['address'] = data['address'].strip() if data['address'] else None
    data['phone_number'] = data['phone_number'].strip() if data['phone_number'] else None
    data['email']= data['email'].strip() if data['email'] else None
    # print(data)

    if (Client.query.filter(Client.name == data['name'], Client.id != user_id).first() is not None):
        return bad_request('There is already a customer with the same name')


    customer.from_dict(data)

    db.session.add(customer)
    db.session.commit()
    
    return jsonify(customer.to_dict(role="customer"))

@bp.route('/supplier/<int:user_id>', methods=['DELETE'])
def delete_supplier(user_id):
    supplier = Client.query.get_or_404(user_id)

    if (supplier.supplier_purchases.first() is not None or supplier.supplier_payments.first() is not None):
        return bad_request('Cannot Delete Supplier. Already had activity with this supplier')

    supplier.categories= []
    db.session.commit()

    db.session.delete(supplier)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/customer/<int:user_id>', methods=['DELETE'])
def delete_customer(user_id):
    customer = Client.query.get_or_404(user_id)

    if (customer.customer_sales.first() is not None or customer.customer_payments.first() is not None):
        return bad_request('Cannot delete Customer. Already had activity with this customer')

    db.session.delete(customer)
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

    purchases_query = db.session.query(Purchase.supplier_id.label("id"), Purchase.total_price.label("total_price"), Purchase.paid.label("paid"))
    payments_query = db.session.query(PaymentSupplier.supplier_id.label("id"), literal(0).label("total_price"), PaymentSupplier.amount.label("paid"))
    union_both = union_all(purchases_query, payments_query).alias("s")

    supliers = db.session.query(Client, func.round(func.ifnull(func.sum(union_both.c.paid), 0),2).label("paid"), func.round(func.ifnull(func.sum(union_both.c.total_price - union_both.c.paid),0),2).label("outstanding") ).outerjoin(union_both, Client.id == union_both.c.id).filter(Client.role == "supplier").group_by(union_both.c.id)
    if(cat != -1):
        supliers = supliers.filter(Client.categories.any(Category.id == cat))


    supliers = supliers.filter(Client.name.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.asc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.asc())
            elif(sorted_field == 'amount_to_get_paid'):
                supliers = supliers.order_by(text("outstanding ASC"))

        else:
            if(sorted_field == 'id'):
                supliers = supliers.order_by(Client.id.desc())
            elif(sorted_field == 'name'):
                supliers = supliers.order_by(Client.name.desc())
            elif(sorted_field == 'amount_to_get_paid'):
                supliers = supliers.order_by(text("outstanding DESC"))
    else:
        supliers = supliers.order_by(Client.id.asc())

    suppliers_with_pag = supliers.paginate(page = curr_page, per_page = per_page,  error_out=True)
    # for item in suppliers_with_pag.items:
    #     print(item)
    items = [item[0].to_dict(role = "supplier", balance=item[1], amount_to_get_paid=item[2]) for item in suppliers_with_pag.items]
    return jsonify({'data':items, 'total':  suppliers_with_pag.total})

@bp.route('/customers/pagination/<int:per_page>')
def get_customers_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    sales_query = db.session.query(Sale.customer_id.label("id"), Sale.total_price.label("total_price"),  func.ifnull(Sale.paid,0).label("paid")).filter(Sale.is_active == True)
    payments_query = db.session.query(PaymentCustomer.customer_id.label("id"), literal(0).label("total_price"), PaymentCustomer.amount.label("paid"))
    union_both = union_all(sales_query, payments_query).alias("s")

    customers = db.session.query(Client, func.round(func.ifnull(func.sum(union_both.c.paid), 0),2).label("paid"), func.round(func.ifnull(func.sum(union_both.c.total_price - union_both.c.paid),0),2).label("outstanding") ).outerjoin(union_both, Client.id == union_both.c.id).filter(Client.role == "customer").group_by(union_both.c.id)
    customers = customers.filter(Client.name.contains(keyword))

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                customers = customers.order_by(Client.id.asc())
            elif(sorted_field == 'name'):
                customers = customers.order_by(Client.name.asc())
            elif(sorted_field == 'amount_to_pay'):
                customers = customers.order_by(text("outstanding ASC"))

        else:
            if(sorted_field == 'id'):
                customers = customers.order_by(Client.id.desc())
            elif(sorted_field == 'name'):
                customers = customers.order_by(Client.name.desc())
            elif(sorted_field == 'amount_to_pay'):
                customers = customers.order_by(text("outstanding DESC"))
    else:
        customers = customers.order_by(Client.id.asc())

    customers_with_pag = customers.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item[0].to_dict(role = "customer", balance=item[1], amount_to_get_paid=item[2]) for item in customers_with_pag.items]
    return jsonify({'data':items, 'total':  customers_with_pag.total})

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

@bp.route('/customers/sales/pagination/<int:cust_id>/<int:per_page>', methods=['POST'])
def get_customer_sales_with_pag(cust_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']
    sale_type = int(data['saletype'])

    customer = Client.query.get_or_404(cust_id)
    sales = customer.customer_sales
    sales = sales.filter(Sale.is_active==True).filter(Sale.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Sale.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sale_type == 1):
        sales = sales.filter(Sale.sale_type == True)
    elif(sale_type == 0):
        sales = sales.filter(Sale.sale_type == False)

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.asc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.asc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.asc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.asc())
            

        else:
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.desc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.desc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.desc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.desc())
    else:
        sales = sales.order_by(Sale.id.asc())

    sales_with_pag = sales.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in sales_with_pag.items]
    return jsonify({'data':items, 'total': sales_with_pag.total})


@bp.route('/supplier/accumulated/<int:supp_id>', methods=['GET'])
def get_supplier_accumulated(supp_id):
    min_month = int(request.args['min_month'])
    min_year = int(request.args['min_year'])

    result = db.session.execute(text("select sum(paid) as total_paid, sum(total_price) as total_price from ( select purchase.id, purchase.date, purchase.paid, purchase.total_price, purchase.supplier_id from purchase where purchase.supplier_id = {} \
                                    and DATE(purchase.date) < '{}-{}-01' union all select payment_supplier.id,  payment_supplier.date,\
                                    payment_supplier.amount, Null as col5, payment_supplier.supplier_id from payment_supplier\
                                    where payment_supplier.supplier_id={} and DATE(payment_supplier.date) < '{}-{}-01') x group by supplier_id;".format(supp_id, min_year, min_month, supp_id, min_year, min_month)))
    res = [dict(row) for row in result]
    if(len(res) > 0):
        return jsonify(res[0])
    else:
        return jsonify({"total_paid": 0, "total_price": 0})

@bp.route('/customer/accumulated/<int:cust_id>', methods=['GET'])
def get_customer_accumulated(cust_id):
    min_month = int(request.args['min_month'])
    min_year = int(request.args['min_year'])

    result = db.session.execute(text("select sum(paid) as total_paid, sum(total_price) as total_price from ( select sale.id, sale.date, ifnull(sale.paid,0) as paid, sale.total_price, sale.customer_id from sale where sale.is_active=true and sale.customer_id = {} \
                                    and DATE(sale.date) < '{}-{}-01' union all select payment_customer.id,  payment_customer.date,\
                                    payment_customer.amount, Null as col5, payment_customer.customer_id from payment_customer\
                                    where payment_customer.customer_id={} and DATE(payment_customer.date) < '{}-{}-01') x group by customer_id;".format(cust_id, min_year, min_month, cust_id, min_year, min_month)))
    res = [dict(row) for row in result]
    if(len(res) > 0):
        return jsonify(res[0])
    else:
        return jsonify({"total_paid": 0, "total_price": 0})

@bp.route('/dates/supplier/activity/<int:supp_id>', methods=['GET'])
def get_dates_range_supplier_activity(supp_id):
    result = db.session.execute(text("select min(min_year) as min_year, max(max_year) as max_year FROM (select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from purchase where supplier_id = {} UNION SELECT min(YEAR(date)) as min_year, max(YEAR(DATE)) as max_year from payment_supplier where supplier_id={}) s".format(supp_id, supp_id)))
    res = [dict(row) for row in result]
    if(len(res) > 0):
        return jsonify(res[0])
    else:
        return jsonify({"min_year": "", "max_year": ""})


@bp.route('/dates/customer/activity/<int:cust_id>', methods=['GET'])
def get_dates_range_customer_activity(cust_id):
    result = db.session.execute(text("select min(min_year) as min_year, max(max_year) as max_year FROM (select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from sale where sale.is_active=true and customer_id = {} UNION SELECT min(YEAR(date)) as min_year, max(YEAR(DATE)) as max_year from payment_customer where customer_id={}) s".format(cust_id, cust_id)))
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

@bp.route('/customers/payments/pagination/<int:cust_id>/<int:per_page>', methods=['POST'])
def get_customer_payments_with_pag(cust_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    customer = Client.query.get_or_404(cust_id)
    payments = customer.customer_payments
    payments = payments.filter(PaymentCustomer.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(PaymentCustomer.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentCustomer.id.asc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentCustomer.date.asc())
            elif(sorted_field == 'amount'):
                payments = payments.order_by(PaymentCustomer.amount.asc())

        else:
            if(sorted_field == 'id'):
                payments = payments.order_by(PaymentCustomer.id.desc())
            elif(sorted_field == 'date'):
                payments = payments.order_by(PaymentCustomer.date.desc())
            elif(sorted_field == 'amount'):
                payments = payments.order_by(PaymentCustomer.amount.desc())
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

@bp.route('/suppliers/outstanding/pagination/<int:per_page>', methods=['POST'])
def get_suppliers_activity_outstanding_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    field_param = None
    order_param = None
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'supplier'):
                field_param = "supplier"
                order_param = "ASC"
            elif(sorted_field == 'latest_date'):
                field_param = "latest_date"
                order_param = "ASC"
            elif(sorted_field == 'outstanding'):
                field_param = "outstanding"
                order_param = "ASC"
        else:
            if(sorted_field == 'supplier'):
                field_param = "supplier"
                order_param = "DESC"
            elif(sorted_field == 'latest_date'):
                field_param = "latest_date"
                order_param = "DESC"
            elif(sorted_field == 'outstanding'):
                field_param = "outstanding"
                order_param = "DESC"
    else:
        field_param = "outstanding"
        order_param = "DESC"

    sql = text("with activity as ((select purchase.supplier_id as id, purchase.total_price as total_price, purchase.paid as paid,\
                (purchase.date) as date, 'purchase' as type from purchase) union all (select payment_supplier.supplier_id as id, 0\
                as total_price, payment_supplier.amount as paid, (payment_supplier.date) as date, 'payment' as type from payment_supplier)\
                ) select m.id, m.max_date as latest_date, m.outstanding, client.name as supplier, type, count(*) over() as Total_count from ( SELECT id , MAX(date)\
                AS max_date, ROUND(IFNULL(SUM(total_price - paid), 0),2) as outstanding FROM activity GROUP BY id) as m inner join\
                activity as t on t.id = m.id and t.date = m.max_date join client on m.id = client.id order by {} {} limit {} , {} ;"\
                .format(field_param, order_param, str((curr_page-1)*per_page), str(per_page)))
    query = db.session.execute(sql)
    if(query is None):
        return bad_request('Something wrong happened from our side')
    res = [dict(row) for row in query]
    # print(res)
    return jsonify({'data':res, 'total': res[0]['Total_count'] if len(res)>0 else 0})

@bp.route('/customers/outstanding/pagination/<int:per_page>', methods=['POST'])
def get_customers_activity_outstanding_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    field_param = None
    order_param = None
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'customer'):
                field_param = "customer"
                order_param = "ASC"
            elif(sorted_field == 'latest_date'):
                field_param = "latest_date"
                order_param = "ASC"
            elif(sorted_field == 'outstanding'):
                field_param = "outstanding"
                order_param = "ASC"
        else:
            if(sorted_field == 'customer'):
                field_param = "customer"
                order_param = "DESC"
            elif(sorted_field == 'latest_date'):
                field_param = "latest_date"
                order_param = "DESC"
            elif(sorted_field == 'outstanding'):
                field_param = "outstanding"
                order_param = "DESC"
    else:
        field_param = "outstanding"
        order_param = "DESC"

    sql = text("with activity as ((select sale.customer_id as id, sale.total_price as total_price, ifnull(sale.paid,0) as paid,\
                (sale.date) as date, 'sale' as type from sale where sale.is_active = true) union all (select payment_customer.customer_id as id, 0\
                as total_price, payment_customer.amount as paid, (payment_customer.date) as date, 'payment' as type from payment_customer)\
                ) select m.id, m.max_date as latest_date, m.outstanding, client.name as customer, type, count(*) over() as Total_count from ( SELECT id , MAX(date)\
                AS max_date, ROUND(IFNULL(SUM(total_price - paid), 0),2) as outstanding FROM activity GROUP BY id) as m inner join\
                activity as t on t.id = m.id and t.date = m.max_date join client on m.id = client.id order by {} {} limit {} , {} ;"\
                .format(field_param, order_param, str((curr_page-1)*per_page), str(per_page)))
    query = db.session.execute(sql)
    if(query is None):
        return bad_request('Something wrong happened from our side')
    res = [dict(row) for row in query]
    # print(res)
    return jsonify({'data':res, 'total': res[0]['Total_count'] if len(res)>0 else 0})

@bp.route('/customer/activity/pagination/<int:cust_id>/<int:per_page>', methods=['POST'])
def get_customer_activity_with_pag(cust_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # keyword = request.args['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']


    customer = Client.query.get_or_404(cust_id)
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

    activity = customer.getActivityQuery(role="customer", field = field_param, order = order_param, page_no = curr_page, rows_per_page = per_page, min_month = filters['min_month'], min_year = filters['min_year'], max_month=filters['max_month'], max_year = filters['max_year'])
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

@bp.route('/customer/activity/print/<int:cust_id>', methods=['POST'])
def get_cust_activity(cust_id):
    data = request.get_json() or {}
    if 'filters' not in data:
        return bad_request('Must include filters')
    filters = data['filters']
    print(filters)
    customer = Client.query.get_or_404(cust_id)
    activity = customer.getActivityPrint(role = "customer", min_month = filters['min_month'], min_year = filters['min_year'], max_month=filters['max_month'], max_year = filters['max_year'])
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

@bp.route('/customer/<int:cust_id>')
def get_customer(cust_id):
    customer = Client.query.get_or_404(cust_id)
    return jsonify(customer.to_dict(role="customer", extraInfo=True))






# @bp.route('/customer/activity/<int:cust_id>')
# def get_cust_activity(cust_id):
#     customer = Client.query.get_or_404(cust_id)
#     activity = customer.getActivity(role = "customer")
#     return jsonify(activity)