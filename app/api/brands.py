from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from sqlalchemy import asc, desc
from sqlalchemy import text
from app.models.brand_model import Brand

@bp.route('/brand/create', methods= ['POST'])
def create_brand():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('must include name field')

    data['name'] = data['name'].strip()

    if Brand.query.filter_by(name=data["name"]).first():
        return bad_request('Brand already exists')
    
    brand = Brand(name = data['name'])
    db.session.add(brand)
    db.session.commit()
    response = jsonify(brand.to_dict())
    response.status_code = 201
    return response

@bp.route('/brands')
def get_brands():
    data = Brand.query.all()
    items = [item.to_dict() for item in data]
    return jsonify(items)