
from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from sqlalchemy.sql import exists, func, text
from app.models.client_model import Client
from app.models.purchase_model import Purchase
from app.models.sale_model import Sale
from app.models.product_model import Product


@bp.route('/dates', methods=['GET'])
def get_dates_range():
    table = (request.args['table']).strip()
    result = None
    if(int(request.args['id'])>0):
        id = int(request.args['id'])
        field = (request.args['field']).strip()
        result = db.engine.execute(text("select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from {} where {}={}".format(table, field, id)))
    else:
        result = db.engine.execute(text("select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from {}".format(table)))
    res = [dict(row) for row in result]
    if(len(res) >0):
        return jsonify(res[0])
    else:
        return jsonify({"min_year": "", "max_year": ""})


@bp.route('/total', methods=['GET'])
def get_total():
    return jsonify({"supplier": Client.query.filter(Client.role == "supplier").count(), "customer": Client.query.filter(Client.role == "customer").count(),
                    "purchase": Purchase.query.count(), "sale": Sale.query.count(), "product": Product.query.count()})