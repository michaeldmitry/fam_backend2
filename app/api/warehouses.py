from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.product_model import Product
from app.models.warehouse_model import Warehouse
from app.models.product_warehouse_model import ProductWarehouse
from sqlalchemy.sql import asc, desc, label, func, text

@bp.route('/warehouse/create', methods= ['POST'])
def add_warehouse():
    data = request.get_json() or {}

    if Warehouse.query.filter_by(name=data["name"]).first():
        return bad_request('Warehouse already exists')
    
    warehouse = Warehouse()
    warehouse.from_dict(data)
    db.session.add(warehouse)
    db.session.commit()
    response = jsonify(warehouse.to_dict())
    response.status_code = 201
    return response

@bp.route('/warehouses')
def get_warehouses():
    warehouses = Warehouse.query.all()
    items = [item.to_dict() for item in warehouses]
    return jsonify(items)

@bp.route('/warehouse/<int:warhouse_id>')
def get_warehouse(warhouse_id):
    warehouse = Warehouse.query.get_or_404(warhouse_id)
    return jsonify(warehouse.to_dict())

@bp.route('/warehouses/pagination/<int:per_page>')
def get_warehouses_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']
    # print(Client.__table__.columns)

    warehouses = Warehouse.query.filter(Warehouse.name.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                warehouses = warehouses.order_by(Warehouse.id.asc())
            elif(sorted_field == 'name'):
                warehouses = warehouses.order_by(Warehouse.name.asc())

        else:
            if(sorted_field == 'id'):
                warehouses = warehouses.order_by(Warehouse.id.desc())
            elif(sorted_field == 'name'):
                warehouses = warehouses.order_by(Warehouse.name.desc())
    else:
        warehouses = warehouses.order_by(Warehouse.id.asc())

    warehouses_with_pag = warehouses.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in warehouses_with_pag.items]
    return jsonify({'data':items, 'total':  warehouses_with_pag.total})

@bp.route('/warehouse/products/pagination/<int:warehouse_id>/<int:per_page>')
def get_warehouse_products_with_pag(warehouse_id, per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    products = Product.query.join(ProductWarehouse).filter(ProductWarehouse.warehouse_id == warehouse_id, ProductWarehouse.quantity > 0)

    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.asc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.asc())
            elif(sorted_field == 'warehouse_quantity'):
                products = products.order_by(text('quantity ASC'))

        else:
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.desc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.desc())
            elif(sorted_field == 'warehouse_quantity'):
                products = products.order_by(text('quantity DESC'))
    else:
        products = products.order_by(Product.part_number.asc())

    products_with_pag = products.paginate(page = curr_page, per_page = per_page,  error_out=True)

    items = [item.to_dict(warehouse_id) for item in products_with_pag.items]
    return jsonify({'data':items, 'total':  products_with_pag.total})