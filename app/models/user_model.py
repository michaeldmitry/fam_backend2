from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import base64
import os
import jwt

class User(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    username = db.Column(db.String(64), unique=True, index=True)
    # email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    token = db.Column(db.String(256), index=True)
    # token_expiration = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    isAdmin = db.Column(db.Boolean, default=False)
    isAccountant = db.Column(db.Boolean, default=False)
    # isDeleted = db.Column(db.Boolean, default=False)
    # orders = db.relationship('Order', backref='user', lazy='dynamic')
    # designerData = db.relationship('DesignerData', backref='user', lazy='dynamic', uselist=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # print(generate_password_hash(password))
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_token(self, expires_in=20000):
        now = datetime.utcnow()
        if self.token:
            return self.token

        payload = {
            # 'exp': now + timedelta(days=0, seconds=expires_in),
            # 'iat': now,
            'sub': self.id
        }
        # print('payload create', payload)
        self.token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')

        # self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    # def revoke_token(self):
    #     self.token_expiration = datetime.utcnow() - timedelta(seconds=1)
        

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        # print(user.to_dict())
        if user is None:
            return None
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
            # print('payload', payload)
            if(payload['sub'] != user.id):
                return None
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        # return user


    def from_dict(self, data, new_user=False):
        for field in ['username']:
            if field in data:
                setattr(self, field, data[field])

        if 'password' in data:
            if data['password'] != '':
                if len((data['password']).strip())>0:
                    self.set_password(data['password'].strip())
        # if new_user:
            # self.set_password(data['password'])
            # self.token = self.get_token()
        
        self.updated_at = datetime.utcnow()


    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'isAdmin': self.isAdmin,
            'isAccountant': self.isAccountant,
            'token': self.token
        }
        return data