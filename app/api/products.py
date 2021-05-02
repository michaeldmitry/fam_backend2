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
from app.models.order_customer_model import OrderCustomer
from app.models.reallocation_model import Reallocation
from app.models.warehouse_model import Warehouse
from app.models.product_warehouse_model import ProductWarehouse
from sqlalchemy.sql import func
from sqlalchemy.sql import asc, desc, label, literal
from sqlalchemy import text
from app.models.subcategory_model import Subcategory
from app.models.brand_model import Brand
from sqlalchemy.orm import aliased
from calendar import monthrange
from app.models.sale_model import Sale


@bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    items = [item.to_dict() for item in products]
    keys = [val for product in products for val in product.attributes.keys() if product.attributes ]
    # for product in products:
    #     if product[0].attributes:
    #         keys.extend(product[0].attributes.keys())
    keys=list(set(keys))

    return jsonify({'products': items, 'attrs': keys})

@bp.route('/product/<int:prod_id>', methods=['DELETE'])
def delete_product(prod_id):
    product = Product.query.get_or_404(prod_id)

    if (product.orders_customer.first() is not None or product.orders_supplier.first() is not None or product.reallocations.first() is not None):
        return bad_request('Product has already been bought, sold, or reallocated')

    product.warehouses= []
    db.session.commit()

    db.session.delete(product)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/product/<int:prod_id>', methods=['PUT'])
def update_product(prod_id):
    data = request.get_json() or {}
    product = Product.query.get_or_404(prod_id)
    data['part_number'] = data['part_number'].strip() if data['part_number'] else None
    data['description'] = data['description'].strip() if data['description'] else None
    data['preorder_level'] = int(data['preorder_level']) if data['preorder_level'] else None

    if (Product.query.filter(Product.part_number == data['part_number'], Product.id != prod_id).first() is not None):
        return bad_request('There is already a product with the same part number')


    product.from_dict(data)

    db.session.add(product)
    db.session.commit()
    
    return jsonify(product.to_dict())

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

@bp.route('/products/search')
def get_special_products_search():
    keyword = request.args['keyword']
    subquery = db.session.query(Product.root_replacement_id).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword)).subquery()
    getAllTreeQ = db.session.query(Product).filter(Product.root_replacement_id.in_(subquery))
    getMatchesQ = db.session.query(Product).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword))
    unionedQ = getAllTreeQ.union(getMatchesQ) 
    products = unionedQ.from_self(Product).all()
    items = [item.to_dict() for item in products]
    return jsonify(items)


@bp.route('/products/pagination/<int:per_page>', methods=['POST'])
def get_products_with_pag(per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search'].strip()
    sorted_field = data['field']
    order = data['order']
    cat = int(data['cat'])
    subcat = int(data['subcat'])
    brand = int(data['brand'])
    attributes = data['attributes']

    subquery = db.session.query(Product.root_replacement_id).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword)).subquery()
    getAllTreeQ = db.session.query(Product).filter(Product.root_replacement_id.in_(subquery))
    getMatchesQ = db.session.query(Product).filter(Product.part_number.contains(keyword) | Product.description.contains(keyword))
    unionedQ = getAllTreeQ.union(getMatchesQ) 
    products = unionedQ.from_self(Product, (func.sum(ProductWarehouse.quantity)+Product.store_qt).label('total')).join(ProductWarehouse).group_by(Product)

    # print(products)

    if(cat != -1):
        products = products.filter(Product.subcategory.has(Subcategory.category_id == cat))
    if(subcat != -1):
        products = products.filter(Product.subcategory_id == subcat)

    if(brand != -1):
        products = products.filter(Product.brand_id == brand)

    # keys = []
    keys = [val for product in products for val in product[0].attributes.keys() if product[0].attributes ]

    # for product in products.all():
    #     if product[0].attributes:
    #         keys.extend(product[0].attributes.keys())
    keys=list(set(keys))
    
    for attr in attributes:
        products = products.filter(Product.attributes, Product.attributes[attr['name']] == attr['value'])


    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.asc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.asc())
            elif(sorted_field == 'total_quantity'):
                products = products.order_by(text('total ASC'))
            elif(sorted_field == 'preorder_level'):
                products = products.order_by(Product.preorder_level.asc())

        else:
            if(sorted_field == 'part_number'):
                products = products.order_by(Product.part_number.desc())
            elif(sorted_field == 'description'):
                products = products.order_by(Product.description.desc())
            elif(sorted_field == 'total_quantity'):
                products = products.order_by(text('total DESC'))
            elif(sorted_field == 'preorder_level'):
                products = products.order_by(Product.preorder_level.desc())
    else:
        products = products.order_by(Product.part_number.asc())

    products_with_pag = products.paginate(page = curr_page, per_page = per_page,  error_out=True)

    products_with_pag_without_total = [item[0] for item in products_with_pag.items]
    items = [item.to_dict() for item in products_with_pag_without_total]
    return jsonify({'data':items, 'total':  products_with_pag.total, 'attr_keys': keys})

@bp.route('/product/purchases/pagination/<int:product_id>/<int:per_page>', methods=['POST'])
def get_product_purchases_with_pag(product_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    product = Product.query.get_or_404(product_id)
    # supplier_orders = product.orders_supplier
    supplier_orders = db.session.query(OrderSupplier, (OrderSupplier.price_per_item * OrderSupplier.quantity).label("total")).filter(OrderSupplier.product_id == product_id)
    supplier_orders = supplier_orders.filter(OrderSupplier.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(OrderSupplier.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'purchase_id'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.purchase_id.asc())
            elif(sorted_field == 'date'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.date.asc())
            elif(sorted_field == 'supplier'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.supplier_id.asc())
            elif(sorted_field == 'quantity'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.quantity.asc())
            elif(sorted_field == 'price_per_item'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.price_per_item.asc())
            elif(sorted_field == 'total'):
                supplier_orders = supplier_orders.order_by(text('total ASC'))

        else:
            if(sorted_field == 'purchase_id'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.purchase_id.desc())
            elif(sorted_field == 'date'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.date.desc())
            elif(sorted_field == 'supplier'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.supplier_id.desc())
            elif(sorted_field == 'quantity'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.quantity.desc())
            elif(sorted_field == 'price_per_item'):
                supplier_orders = supplier_orders.order_by(OrderSupplier.price_per_item.desc())
            elif(sorted_field == 'total'):
                supplier_orders = supplier_orders.order_by(text('total DESC'))
    else:
        supplier_orders = supplier_orders.order_by(OrderSupplier.id.asc())

    supplier_orders_with_pag = supplier_orders.paginate(page = curr_page, per_page = per_page,  error_out=True)
    supplier_orders_with_pag_without_total = [item[0] for item in supplier_orders_with_pag.items]

    items = [item.to_dict() for item in supplier_orders_with_pag_without_total]
    return jsonify({'data':items, 'total': supplier_orders_with_pag.total})

@bp.route('/product/sales/pagination/<int:product_id>/<int:per_page>', methods=['POST'])
def get_product_sales_with_pag(product_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    product = Product.query.get_or_404(product_id)
    # supplier_orders = product.orders_supplier
    customer_orders = db.session.query(OrderCustomer, (OrderCustomer.price_per_item * OrderCustomer.quantity).label("total")).filter(OrderCustomer.product_id == product_id).filter(OrderCustomer.sale.has(Sale.is_active == True))
    customer_orders = customer_orders.filter(OrderCustomer.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(OrderCustomer.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'sale_id'):
                customer_orders = customer_orders.order_by(OrderCustomer.sale_id.asc())
            elif(sorted_field == 'date'):
                customer_orders = customer_orders.order_by(OrderCustomer.date.asc())
            elif(sorted_field == 'customer'):
                customer_orders = customer_orders.order_by(OrderCustomer.customer_id.asc())
            elif(sorted_field == 'quantity'):
                customer_orders = customer_orders.order_by(OrderCustomer.quantity.asc())
            elif(sorted_field == 'price_per_item'):
                customer_orders = customer_orders.order_by(OrderCustomer.price_per_item.asc())
            elif(sorted_field == 'total'):
                customer_orders = customer_orders.order_by(text('total ASC'))

        else:
            if(sorted_field == 'sale_id'):
                customer_orders = customer_orders.order_by(OrderCustomer.sale_id.desc())
            elif(sorted_field == 'date'):
                customer_orders = customer_orders.order_by(OrderCustomer.date.desc())
            elif(sorted_field == 'customer'):
                customer_orders = customer_orders.order_by(OrderCustomer.customer_id.desc())
            elif(sorted_field == 'quantity'):
                customer_orders = customer_orders.order_by(OrderCustomer.quantity.desc())
            elif(sorted_field == 'price_per_item'):
                customer_orders = customer_orders.order_by(OrderCustomer.price_per_item.desc())
            elif(sorted_field == 'total'):
                customer_orders = customer_orders.order_by(text('total DESC'))
    else:
        customer_orders = customer_orders.order_by(OrderCustomer.id.asc())

    customer_orders_with_pag = customer_orders.paginate(page = curr_page, per_page = per_page,  error_out=True)
    customer_orders_with_pag_without_total = [item[0] for item in customer_orders_with_pag.items]

    items = [item.to_dict() for item in customer_orders_with_pag_without_total]
    return jsonify({'data':items, 'total': customer_orders_with_pag.total})


@bp.route('/product/reallocations/pagination/<int:product_id>/<int:per_page>', methods=['POST'])
def get_product_reallocations_with_pag(product_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    product = Product.query.get_or_404(product_id)
    reallocations = product.reallocations
    reallocations = reallocations.filter(Reallocation.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Reallocation.date <= '{}-{:02d}-{:02d} 23:59:59'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    

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

    data['part_number'] = data['part_number'].strip().upper()
    
    subcategory = Subcategory.query.get_or_404(subcat_id)
    brand = Brand.query.get_or_404(brand_id)

    if Product.query.filter_by(part_number=data["part_number"]).first():
        return bad_request('Product already exists')

    if('preorder_level' in data):
        data['preorder_level'] = int(data['preorder_level'])
    else:
        data['preorder_level'] = 0
    
    if('store_qt' in data):
        data['store_qt'] = int(data['store_qt'])
    else:
        data['store_qt'] = 0

    replacement=None

    if 'replacement' in data and data['replacement']:
        replacement = Product.query.get_or_404(int(data['replacement']))

    if 'description' in data and data['description']:
        data['description'] = data['description'].strip()

    
    product = Product(store_qt = data['store_qt'], description = data['description'], part_number = data['part_number'], preorder_level = data['preorder_level'], subcategory=subcategory, brand=brand, attributes= data['attributes'])
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

@bp.route('/product/attr/values')
def get_product_attr_values():
    key = request.args['key']
    products = Product.query.all()
    vals = []
    for product in products:
        if product.attributes and key in product.attributes and product.attributes[key] not in vals:
            vals.append(product.attributes[key])
    return jsonify(list(vals))