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
from app.models.order_supplier_model import OrderSupplier
from app.models.reallocation_model import Reallocation
from app.models.warehouse_model import Warehouse
from app.models.product_warehouse_model import ProductWarehouse
from sqlalchemy.sql import func
from sqlalchemy.sql import asc, desc, label, literal
from sqlalchemy import text
from app.models.subcategory_model import Subcategory
from app.models.brand_model import Brand
from sqlalchemy.orm import aliased


@bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    items = [item.to_dict() for item in products]
    return jsonify(items)

@bp.route('/products/dropdown', methods=['GET'])
def get_products_dropdown():
    products = Product.query.all()
    items = [item.to_dict_drop() for item in products]
    return jsonify(items)

@bp.route('/product/<int:product_id>')
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@bp.route('/product/quantity/<int:product_id>')
def get_product_quantities(product_id):
    product = Product.query.get_or_404(product_id)
    data = []
    store_item ={ 'name': 'Store Quantity', 'val':product.store_qt }
    # store_item = {'Store Quantity':product.store_qt}
    data.append(store_item)

    warehouses = product.warehouses.all()
    for ind, warehouse in enumerate(warehouses):
        quantity = ProductWarehouse.query.filter(ProductWarehouse.product_id == product.id, ProductWarehouse.warehouse_id == warehouse.id).first().quantity
        if(quantity is not None and quantity > 0):
            name = 'Warehouse'+str(warehouse.id)+" Quantity"
            wh_item = {'name': name, 'val': quantity}
            data.append(wh_item)

    return jsonify(data)


@bp.route('/products/preorder/pagination/<int:per_page>', methods=['GET'])
def get_products_below_preorder(per_page):
    curr_page = int(request.args['current'])
    products = db.session.query(Product, (func.sum(ProductWarehouse.quantity)+Product.store_qt).label('total')).join(ProductWarehouse).group_by(Product)
    products = products.having(text("total <= preorder_level"))

    products_with_pag = products.paginate(page = curr_page, per_page = per_page,  error_out=True)

    products_with_pag_without_total = [item[0] for item in products_with_pag.items]
    # print(products_with_pag_without_total)
    items = [item.to_dict() for item in products_with_pag_without_total]
    return jsonify({'data':items, 'total':  products_with_pag.total})

@bp.route('/products/pagination/<int:per_page>')
def get_products_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search'].strip()
    sorted_field = request.args['field']
    order = request.args['order']
    cat = int(request.args['cat'])
    subcat = int(request.args['subcat'])

    subquery = db.session.query(Product.root_replacement_id).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword)).subquery()
    getAllTreeQ = db.session.query(Product).filter(Product.root_replacement_id.in_(subquery))
    getMatchesQ = db.session.query(Product).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword))
    unionedQ = getAllTreeQ.union(getMatchesQ) 
    products = unionedQ.from_self(Product, (func.sum(ProductWarehouse.quantity)+Product.store_qt).label('total')).join(ProductWarehouse).group_by(Product)


    if(cat != -1):
        products = products.filter(Product.subcategory.has(Subcategory.category_id == cat))
    if(subcat != -1):
        products = products.filter(Product.subcategory_id == subcat)

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.asc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.asc())
            elif(sorted_field == 'total_quantity'):
                products = products.order_by(text('total ASC'))

        else:
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.desc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.desc())
            elif(sorted_field == 'total_quantity'):
                products = products.order_by(text('total DESC'))
    else:
        products = products.order_by(Product.part_number.asc())

    products_with_pag = products.paginate(page = curr_page, per_page = per_page,  error_out=True)

    products_with_pag_without_total = [item[0] for item in products_with_pag.items]
    items = [item.to_dict() for item in products_with_pag_without_total]
    return jsonify({'data':items, 'total':  products_with_pag.total})

@bp.route('/product/purchases/pagination/<int:product_id>/<int:per_page>')
def get_product_purchases_with_pag(product_id,per_page):
    curr_page = int(request.args['current'])
    sorted_field = request.args['field']
    order = request.args['order']

    product = Product.query.get_or_404(product_id)
    supplier_orders = product.orders_supplier

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.id.asc())
            elif(sorted_field == 'date'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.date.asc())
            elif(sorted_field == 'supplier'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.supplier_id.asc())

        else:
            if(sorted_field == 'id'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.id.desc())
            elif(sorted_field == 'date'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.date.desc())
            elif(sorted_field == 'supplier'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.supplier_id.desc())
    else:
        supplier_orders = supplier_orders.order_by(OrderSupplier.id.asc())

    supplier_orders_with_pag = supplier_orders.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in supplier_orders_with_pag.items]
    return jsonify({'data':items, 'total': supplier_orders_with_pag.total})

@bp.route('/product/reallocations/pagination/<int:product_id>/<int:per_page>')
def get_product_reallocations_with_pag(product_id,per_page):
    curr_page = int(request.args['current'])
    sorted_field = request.args['field']
    order = request.args['order']

    product = Product.query.get_or_404(product_id)
    reallocations = product.reallocations

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                reallocations = reallocations.order_by(Reallocation.id.asc())
            elif(sorted_field == 'date'):
                reallocations = reallocations.order_by(Reallocation.date.asc())
            elif(sorted_field == 'quantity'):
                reallocations = reallocations.order_by(Reallocation.quantity.asc())

        else:
            if(sorted_field == 'id'):
                reallocations = reallocations.order_by(Reallocation.id.desc())
            elif(sorted_field == 'date'):
                reallocations = reallocations.order_by(Reallocation.date.desc())
            elif(sorted_field == 'quantity'):
                reallocations = reallocations.order_by(Reallocation.quantity.desc())
    else:
        reallocations = reallocations.order_by(Reallocation.id.asc())

    reallocations_with_pag = reallocations.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in reallocations_with_pag.items]
    return jsonify({'data':items, 'total': reallocations_with_pag.total})

@bp.route('/product/create/<int:subcat_id>/<int:brand_id>', methods= ['POST'])
def add_product(subcat_id, brand_id):
    data = request.get_json() or {}
    if 'description' not in data or 'part_number' not in data:
        return bad_request('must include item part number & description fields')

    data['part_number'] = data['part_number'].strip()
    
    subcategory = Subcategory.query.get_or_404(subcat_id)
    brand = Brand.query.get_or_404(brand_id)

    if Product.query.filter_by(part_number=data["part_number"]).first():
        return bad_request('Product already exists')

    if('preorder_level' in data):
        data['preorder_level'] = int(data['preorder_level'])
    else:
        data['preorder_level'] = 0
    
    replacement=None

    if 'replacement' in data and data['replacement']:
        replacement = Product.query.get_or_404(int(data['replacement']))

    if 'description' in data and data['description']:
        data['description'] = data['description'].strip()
    
    product = Product(description = data['description'], part_number = data['part_number'], preorder_level = data['preorder_level'], subcategory=subcategory, brand=brand)
    if(replacement):
        replacement.replaced_by.append(product)
        rootReplacement = db.session.query(Product).from_statement(text(''' 
                                                                with recursive cteUp as (
                                                                        select     *
                                                                        from product
                                                                        where  id ={}
                                                                        union all
                                                                        select     p.*
                                                                        from       product p
                                                                        inner join cteUp
                                                                        on p.id= cteUp.replaces_id
                                                                        )
                                                            select * from cteUp where id = (select MIN(id) from cteUp);  
        
        '''.format(str(data['replacement'])))).first()
        product.root_replacement_id = rootReplacement.id
        replacement.root_replacement_id = rootReplacement.id
        
        db.session.add(replacement)

    warehouses = Warehouse.query.all()
    for warehouse in warehouses:
        product.warehouses.append(warehouse)


    db.session.add(product)
    db.session.commit()
    response = jsonify(product.to_dict())
    response.status_code = 201
    return response