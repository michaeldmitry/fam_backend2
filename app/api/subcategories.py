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
from app.models.category_model import Category
from app.models.subcategory_model import Subcategory

@bp.route('/subcategory/create/<int:category_id>', methods= ['POST'])
def create_subcategory(category_id):
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('must include name field')

    data['name'] = data['name'].strip()

    category = Category.query.get_or_404(category_id)

    if Subcategory.query.filter_by(name=data["name"]).first():
        return bad_request('Subcategory already exists')
    
    subcategory = Subcategory(name = data['name'], category = category)
    db.session.add(subcategory)
    db.session.commit()
    response = jsonify(subcategory.to_dict())
    response.status_code = 201
    return response

@bp.route('/subcategories/<int:category_id>')
def get_subcategories(category_id):
    category = Category.query.get_or_404(category_id)
    data = category.subcategories.all()
    items = [item.to_dict() for item in data]
    return jsonify(items)