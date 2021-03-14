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
from app.models.reallocation_model import Reallocation
from app.models.warehouse_model import Warehouse
from app.models.product_warehouse_model import ProductWarehouse
from calendar import monthrange


@bp.route('/reallocation/<int:re_id>', methods=['DELETE'])
def delete_reallocation(re_id):
    reallocation = Reallocation.query.get_or_404(re_id)
    product = reallocation.product

    if(reallocation.from_loc == "store"):
        product.store_qt = product.store_qt+reallocation.quantity
        to_warehouse = ProductWarehouse.query.filter(ProductWarehouse.product_id == product.id, ProductWarehouse.warehouse_id == reallocation.to_warehouse_id).first()
        if(to_warehouse.quantity < reallocation.quantity):
            return bad_request('Cannot delete reallocation. Warehouse doesnt have enough quantity')
        to_warehouse.quantity = to_warehouse.quantity - reallocation.quantity
        db.session.add(to_warehouse)
    else:
        from_warehouse = ProductWarehouse.query.filter(ProductWarehouse.product_id == product.id, ProductWarehouse.warehouse_id == reallocation.from_warehouse_id).first()
        from_warehouse.quantity = from_warehouse.quantity+reallocation.quantity
        if(reallocation.to_loc == "warehouse"):
            to_warehouse = ProductWarehouse.query.filter(ProductWarehouse.product_id == product.id, ProductWarehouse.warehouse_id == reallocation.to_warehouse_id).first()
            if(to_warehouse.quantity < reallocation.quantity):
                return bad_request('Cannot delete reallocation. Warehouse doesnt have enough quantity')
            to_warehouse.quantity = to_warehouse.quantity - reallocation.quantity
            db.session.add(to_warehouse)
        else:
            if(product.store_qt < reallocation.quantity):
                return bad_request('Cannot delete reallocation. Store doesnt have enough quantity')
            product.store_qt = product.store_qt - reallocation.quantity
        db.session.add(from_warehouse)


    db.session.add(product)
    db.session.delete(reallocation)
    db.session.commit()
    return jsonify({"message": "deleted successfully"})

@bp.route('/reallocation/store/create/<int:product_id>', methods= ['POST'])
def reallocate_product_store(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    if 'to_warehouse_id' not in data or 'quantity' not in data:
        return bad_request('must include warehouse & quantity fields')

    data['quantity'] = int(data['quantity'])
    data['to_warehouse_id'] = int(data['to_warehouse_id'])

    if(data['quantity']<=0):
        return bad_request('Invalid quantity')
    
    quantity_available = product.check_store_availability(data['quantity'])

    if(quantity_available == False):
        return bad_request('Not enough product quantity in the store')

    product.store_qt = product.store_qt - data['quantity']
    if(product.store_qt == 0):
        product.store_loc = "None"

    product_warehouse = ProductWarehouse()
    product_warehouse = product_warehouse.reallocate_from_store(quantity = data['quantity'] , product_id = product_id, to_warehouse_id = data['to_warehouse_id'] , location=data['location'])
    
    reallocation = Reallocation(quantity = data['quantity'], from_loc= "store", to_loc = "warehouse", product = product, to_warehouse_id = data['to_warehouse_id'])

    db.session.add(product)
    db.session.add(product_warehouse)
    db.session.add(reallocation)
    db.session.commit()

    response = jsonify(reallocation.to_dict())
    response.status_code = 201
    return response

@bp.route('/reallocation/warehouse/create/<int:product_id>', methods= ['POST'])
def reallocate_product_warehouse(product_id):
    product = Product.query.get_or_404(product_id)

    data = request.get_json() or {}
    if 'from_warehouse_id' not in data or 'to' not in data or 'quantity' not in data:
        return bad_request('must include warehouses & quantity fields')

    data['quantity'] = int(data['quantity'])
    data['from_warehouse_id'] = int(data['from_warehouse_id'])

    if(data['quantity']<=0):
        return bad_request('Invalid quantity')

    
    from_warehouse = ProductWarehouse.query.filter(ProductWarehouse.product_id == product_id , ProductWarehouse.warehouse_id == data['from_warehouse_id']).first()
    # print(from_warehouse.quantity, data['quantity'], from_warehouse.quantity >= data['quantity'])
    # return bad_request('h')
    if(not(from_warehouse.quantity >= data['quantity'])):
        return bad_request('Not enough product quantity in Warehouse')

    from_warehouse.quantity = from_warehouse.quantity - data['quantity']
    if(from_warehouse.quantity == 0):
        from_warehouse.location = "None"

    product_warehouse = ProductWarehouse()

    if(data['to'] == 'store'):
        product.store_qt = product.store_qt + data['quantity']
        if(data['location'] != 'N/A'):
            product.store_loc = data['location']

        reallocation = Reallocation(quantity = data['quantity'], from_loc= "warehouse", to_loc = "store", product = product, from_warehouse_id = data['from_warehouse_id'])

        db.session.add(reallocation)

    elif(data['to'] == 'warehouse'):
        if 'to_warehouse_id' not in data:
            return bad_request('Must include warehouse info')

        data['to_warehouse_id'] = int(data['to_warehouse_id'])

        if(data['from_warehouse_id'] == data['to_warehouse_id']):
            return bad_request('Cannot reallocate from and to the same place')

        to_warehouse = product_warehouse.reallocate_from_warehouse(quantity = data['quantity'] , product_id = product_id, to_warehouse_id = data['to_warehouse_id'] , location=data['location'])
        reallocation = Reallocation(quantity = data['quantity'], from_loc= "warehouse", to_loc = "warehouse", product = product, from_warehouse_id = data['from_warehouse_id'], to_warehouse_id = data['to_warehouse_id'])
        db.session.add(reallocation)
        db.session.add(to_warehouse)


    else:
        return bad_request('Invalid Operation')

    
    db.session.add(product)
    db.session.add(from_warehouse)

    db.session.commit()

    response = jsonify({'success':True})
    response.status_code = 201
    return response

@bp.route('/reallocations')
def get_reallocations():
    reallocations = Reallocation.query.all()
    items = [item.to_dict() for item in reallocations]
    return jsonify(items)

@bp.route('/reallocations/pagination/<int:per_page>', methods=['POST'])
def get_reallocations_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    reallocations = Reallocation.query.filter(Reallocation.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Reallocation.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    reallocations = reallocations.filter(Reallocation.product.has(Product.part_number.contains(keyword)))


    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                reallocations = reallocations.order_by(Reallocation.id.asc())
            elif(sorted_field == 'date'):
                reallocations = reallocations.order_by(Reallocation.date.asc())
            elif(sorted_field == 'product'):
                reallocations = reallocations.order_by(Reallocation.product_id.asc())

        else:
            if(sorted_field == 'id'):
                reallocations = reallocations.order_by(Reallocation.id.desc())
            elif(sorted_field == 'date'):
                reallocations = reallocations.order_by(Reallocation.date.desc())
            elif(sorted_field == 'product'):
                reallocations = reallocations.order_by(Reallocation.product_id.desc())
    else:
        reallocations = reallocations.order_by(Reallocation.id.asc())

    reallocations_with_pag = reallocations.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in reallocations_with_pag.items]
    return jsonify({'data':items, 'total':  reallocations_with_pag.total})