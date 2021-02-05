
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


@bp.route('/dates', methods=['GET'])
def get_dates_range():
    table = (request.args['table']).strip()
    result = db.engine.execute(text("select min(YEAR(date)) as min_year, max(YEAR(date)) as max_year from {}".format(table)))
    res = [dict(row) for row in result]
    return jsonify(res[0])