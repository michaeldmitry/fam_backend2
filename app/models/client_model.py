from datetime import datetime
from app import db
from .purchase_model import Purchase
from .payment_supplier_model import PaymentSupplier
from .order_supplier_model import OrderSupplier
from .sale_model import Sale
from .payment_customer_model import PaymentCustomer
from .order_customer_model import OrderCustomer
from .return_purchase_model import ReturnPurchase
from .return_sale_model import ReturnSale
from .order_supplier_return_model import OrderSupplierReturn
from .order_customer_return_model import OrderCustomerReturn
from sqlalchemy.sql.expression import label
from sqlalchemy import text

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(10))

    supplier_balance = db.Column(db.Float, default=0.0)
    customer_balance = db.Column(db.Float, default=0.0)
    amount_to_pay = db.Column(db.Float, default=0.0)
    amount_to_get_paid = db.Column(db.Float, default=0.0)

    # accounts = db.relationship('Account', secondary = 'client_account' , lazy='dynamic')
    email = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(64))

    supplier_purchases = db.relationship('Purchase', backref='supplier', lazy='dynamic')
    supplier_payments = db.relationship('PaymentSupplier', backref='supplier', lazy='dynamic')
    supplier_orders = db.relationship('OrderSupplier', backref='supplier', lazy='dynamic')

    customer_sales = db.relationship('Sale', backref='customer', lazy='dynamic')
    customer_payments = db.relationship('PaymentCustomer', backref='customer', lazy='dynamic')
    customer_orders = db.relationship('OrderCustomer', backref='customer', lazy='dynamic')

    supplier_returns = db.relationship('ReturnPurchase', backref = 'supplier' , lazy='dynamic')
    supplier_order_returns = db.relationship('OrderSupplierReturn', backref='supplier', lazy='dynamic')

    customer_returns = db.relationship('ReturnSale', backref = 'customer' , lazy='dynamic')
    customer_order_returns = db.relationship('OrderCustomerReturn', backref='customer', lazy='dynamic')

    def to_dict(self, role, extraInfo=False):
        data = {
            'id': self.id,
            'name': self.name
        }
        if(role == "customer"):
            data['customer_balance'] = self.customer_balance
            data['amount_to_pay'] = self.amount_to_pay
        elif(role == "supplier"):
            data['supplier_balance'] = self.supplier_balance
            data['amount_to_get_paid'] = self.amount_to_get_paid

        if(extraInfo):
            data['email'] = self.email
            data['phone_number'] = self.phone_number
            data['address'] = self.address
               
        return data


    def getActivity(self, role):
        activity = []
        if(role == "supplier"):
            purchases = self.supplier_purchases.all()
            purchases_list = [item.to_dict() for item in purchases]

            payments  = self.supplier_payments.all()
            payments_list = [item.to_dict() for item in payments]

            purchases_list.extend(payments_list)
            activity = sorted(purchases_list, key=lambda x: x['date'])

        elif( role == "customer"):
            sales = self.customer_sales.all()
            sales_list = [item.to_dict() for item in sales]

            payments  = self.customer_payments.all()
            payments_list = [item.to_dict() for item in payments]

            sales_list.extend(payments_list)
            activity = sorted(sales_list, key=lambda x: x['date'])

        return activity

    def getActivityQuery(self, role, field, order, page_no, rows_per_page):
        
        if(role == "supplier"):
            id = self.id
            sql = text("SELECT id, date, paid, total_price, COUNT(*) OVER() AS Total_count FROM ((select purchase.id, purchase.date, purchase.paid, purchase.total_price from purchase where purchase.supplier_id = \
                     {}) union all (select payment_supplier.id,  payment_supplier.date,payment_supplier.amount, Null as col5 from payment_supplier\
                     where payment_supplier.supplier_id={})) s order by {} {} LIMIT {}, {};".format(str(id), str(id), field, order, str((page_no-1)*rows_per_page), str(rows_per_page) ))

            both = db.engine.execute(sql)
            return both

        elif( role == "customer"):
            id = self.id
            sql = text("SELECT id, date, paid, total_price, COUNT(*) OVER() AS Total_count FROM ((select sale.id, sale.date, sale.paid, sale.total_price from sale where sale.customer_id = \
                     {}) union all (select payment_customer.id,  payment_customer.date,payment_customer.amount, Null as col5 from payment_customer\
                     where payment_customer.customer_id={})) s order by {} {} LIMIt {}, {};".format(str(id), str(id), field, order,  str((page_no-1)*rows_per_page), str(rows_per_page) ))

            both = db.engine.execute(sql)
            return both
        else:
            return None