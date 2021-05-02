from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.sale_draft_model import SaleDraft
from sqlalchemy.sql import exists, func, text
from datetime import date, timedelta
from calendar import monthrange



@bp.route('/sale/draft/create', methods=['POST'])
def add_sale_draft():
    data = request.get_json() or {}

    if 'orders' not in data or 'total_price' not in data or 'taxes_add' not in data or 'reduction_add' not in data or 'official' not in data or 'customer_id' not in data or 'employees' not in data:
        return bad_request('Incomplete Info')


    orders = data['orders']
    total_price = float(data['total_price'])
    official = True if int(data['official']) ==1 else False
    taxes_add = True if int(data['taxes_add']) == 1 else False
    reduction_add = True if int(data['reduction_add']) == 1 else False
    customer_id = str(data['customer_id'])
    representative_name =  data['representative_name'] 
    representative_number = data['representative_number']
    representative_email = data['representative_email']
    employees = data['employees']

    saleDraft = SaleDraft(total_price = total_price, official = official, orders = orders, taxes_add = taxes_add, reduction_add= reduction_add, customer_id=customer_id,representative_email=representative_email, representative_name=representative_name, representative_number=representative_number, employees_belong=employees)

    db.session.add(saleDraft)
    db.session.commit()
    return jsonify(saleDraft.to_dict())

@bp.route('/sales/drafts/pagination/<int:per_page>', methods=['POST'])
def get_sales_drafts_with_pag(per_page):
    # print('here')
    data = request.get_json() or {}
    curr_page = int(data['current'])
    # print(curr_page)
    salesDrafts = SaleDraft.query.order_by(SaleDraft.date.desc())

    sales_with_pag = salesDrafts.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in sales_with_pag.items]
    return jsonify({'data':items, 'total':  sales_with_pag.total})

@bp.route('/sale/draft/<int:sale_id>', methods=['DELETE'])
def delete_sale_draft(sale_id):
    saleDraft = SaleDraft.query.get_or_404(sale_id)
    db.session.delete(saleDraft)

    db.session.commit()
    
    return jsonify({"message":"deleted successfully"})

@bp.route('/sale/draft/total', methods=['GET'])
def get_sale_draft_total():
    count = SaleDraft.query.count()
    data = {}
    if(count == 1):
        data = SaleDraft.query.first().to_dict()
    return jsonify({"count": count, "data": data})