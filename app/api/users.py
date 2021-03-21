from app.api import bp
from app.models.user_model import User
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
from app.api.auth import token_auth
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from random import randint
from flask import current_app
from app.api.auth import basic_auth


@bp.route('/user/signin', methods=['POST'])
@basic_auth.login_required
def user_sign_in():
    token = g.current_user.get_token()
    db.session.commit()
    reply = {
        'token': token,
        'id': g.current_user.id,
        'username': g.current_user.username,
        'isAdmin': g.current_user.isAdmin,
        'isAccountant':g.current_user.isAccountant
    }
    return jsonify(reply)

@bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    
    if 'username' not in data or 'password' not in data:
        return bad_request('must include username & password fields')

    data['password'] = str(data['password'])
    data['password'] = data['password'].strip()
    data['username'] = data['username'].strip()

    if(data['username'] == "" or data['password'] == ""):
        return bad_request('must include username, and password fields')

    
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')

    # if 'isAdmin' in data:
    #     if(data['isAdmin'] == "true"):
    #         data['isAdmin'] = True
    #     else:
    #         data['isAdmin'] = False
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    user.token = user.get_token()
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    return response