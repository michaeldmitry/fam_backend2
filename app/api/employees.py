from app.api import bp
from flask import jsonify
from app.helpers.errors import bad_request
from app.helpers.errors import error_response
from flask import request
from app import db
from flask import url_for
from flask import g, abort
import uuid
from app.models.employee_model import Employee
from datetime import date, timedelta, datetime
from calendar import monthrange
from app.models.sale_employee_association_table import sale_employee_association_table
from app.models.client_model import Client
from app.models.sale_model import Sale
from sqlalchemy.sql import exists, func, text


@bp.route('/employees')
def get_employees():
    employees = Employee.query.all()
    res = [item.to_dict() for item in employees]
    return jsonify(res)

@bp.route('/employee/<int:emp_id>')
def get_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    return jsonify(employee.to_dict())

@bp.route('/employee/<int:user_id>', methods=['DELETE'])
def delete_employee(user_id):
    employee = Employee.query.get_or_404(user_id)

    employee.sales= []
    db.session.commit()

    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({"message": "deleted successfully"})

@bp.route('/employee/<int:user_id>', methods=['PUT'])
def update_employee(user_id):
    data = request.get_json() or {}
    employee = Employee.query.get_or_404(user_id)

    # if data['fullname']
    data['fullname'] = data['fullname'].strip() if data['fullname'] else None
    data['address'] = data['address'].strip() if data['address'] else None
    data['phone'] = data['phone'].strip() if data['phone'] else None
    data['title']= data['title'].strip() if data['title'] else None
    data['id_number']= data['id_number'].strip() if data['id_number'] else None
    data['insurance_number']= data['insurance_number'].strip() if data['insurance_number'] else None
    data['employment_date']= datetime.strptime(data['employment_date'], '%Y-%m-%d') if data['employment_date'] else None
    data['fixed_salary']= int(data['fixed_salary']) if data['fixed_salary'] else None
    data['variable_salary']= int(data['variable_salary']) if data['variable_salary'] else None

    if (Employee.query.filter(Employee.fullname == data['fullname'], Employee.id != user_id).first() is not None):
        return bad_request('There is already an employee with the same name')


    employee.from_dict(data)

    db.session.add(employee)
    db.session.commit()
    
    return jsonify(employee.to_dict())

@bp.route('/employees/pagination/<int:per_page>')
def get_employees_with_pag(per_page):
    curr_page = int(request.args['current'])
    keyword = request.args['search']
    sorted_field = request.args['field']
    order = request.args['order']

    employees = Employee.query

    employees = employees.filter(Employee.fullname.contains(keyword))
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                employees = employees.order_by(Employee.id.asc())
            elif(sorted_field == 'fullname'):
                employees = employees.order_by(Employee.fullname.asc())

        else:
            if(sorted_field == 'id'):
                employees = employees.order_by(Employee.id.desc())
            elif(sorted_field == 'fullname'):
                employees = employees.order_by(Employee.fullname.desc())

    else:
        employees = employees.order_by(Employee.id.asc())

    employees_with_pag = employees.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in employees_with_pag.items]
    return jsonify({'data':items, 'total':  employees_with_pag.total})

@bp.route('/employees/sales/total/pagination/<int:per_page>')
def get_employees_sales_with_pag(per_page):
    # data = request.get_json() or {}
    curr_page = int(request.args['current'])
    order = request.args['order']
    sorted_field = request.args['field']
    
    employees = db.session.query(Employee.id, Employee.fullname, func.count(sale_employee_association_table.c.sale_id).label("total_sales")).outerjoin(sale_employee_association_table, Employee.id == sale_employee_association_table.c.employee_id).outerjoin(Sale, sale_employee_association_table.c.sale_id == Sale.id).filter(Sale.is_active == True).group_by(Employee.id)
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'fullname'):
                employees = employees.order_by(Employee.fullname.asc())
            elif(sorted_field == 'total_sales'):
                employees = employees.order_by(text("total_sales ASC"))
        else:
            if(sorted_field == 'fullname'):
                employees = employees.order_by(Employee.fullname.desc())
            elif(sorted_field == 'total_sales'):
                employees = employees.order_by(text("total_sales DESC"))
    else:
        employees = employees.order_by(text("total_sales DESC"))

    emps_with_pag = employees.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [{"id": item[0], "fullname": item[1], "total_sales": item[2]} for item in emps_with_pag.items]
    return jsonify({'data':items, 'total':  emps_with_pag.total})

@bp.route('/employee/sales/<int:emp_id>/pagination/<int:per_page>', methods=['POST'])
def get_employee_sales_with_pag(emp_id,per_page):
    data = request.get_json() or {}
    curr_page = int(data['current'])
    keyword = data['search']
    sorted_field = data['field']
    order = data['order']
    filters = data['filters']

    sales = db.session.query(Sale).join(sale_employee_association_table, sale_employee_association_table.c.sale_id == Sale.id).filter(Sale.is_active == True).filter(sale_employee_association_table.c.employee_id == emp_id)
    sales = sales.filter(Sale.date >= '{}-{:02d}-01'.format(filters['min_year'], filters['min_month'])).filter(Sale.date <= '{}-{:02d}-{:02d}'.format(filters['max_year'], filters['max_month'], monthrange(filters['max_year'],filters['max_month'])[1]))    
    sales = sales.filter(Sale.customer.has(Client.name.contains(keyword)))
    
    if(sorted_field != "" and order !=""):
        if(order == "asc"):
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.asc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.asc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.asc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.asc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.asc())
        else:
            if(sorted_field == 'id'):
                sales = sales.order_by(Sale.id.desc())
            elif(sorted_field == 'date'):
                sales = sales.order_by(Sale.date.desc())
            elif(sorted_field == 'customer'):
                sales = sales.order_by(Sale.customer_id.desc())
            elif(sorted_field == 'total_price'):
                sales = sales.order_by(Sale.total_price.desc())
            elif(sorted_field == 'paid'):
                sales = sales.order_by(Sale.paid.desc())
    else:
        sales = sales.order_by(Sale.id.asc())

    sales_with_pag = sales.paginate(page = curr_page, per_page = per_page,  error_out=True)
    items = [item.to_dict() for item in sales_with_pag.items]
    return jsonify({'data':items, 'total':  sales_with_pag.total})

@bp.route('/employee', methods=['POST'])
def add_employee():
    data = request.get_json() or {}
    if not data['fullname']  or not data['title']:
        return bad_request('Must include Full Name & Title')
    else:
        data['fullname'] = data['fullname'] .strip()
        data['title'] = data['title'].strip()

    
    data['address'] = data['address'].strip() if data['address'] else None
    data['fixed_salary'] = int(data['fixed_salary']) if data['fixed_salary'] else None
    data['variable_salary'] = int(data['variable_salary']) if data['variable_salary'] else None
    if data['employment_date']:
        # print("Yes")
        data['employment_date'] = datetime.strptime(data['employment_date'], '%Y-%m-%d')
    else:
        data['employment_date'] = None
    data['phone'] = data['phone'].strip() if data['phone'] else None
    data['insurance_number'] = data['insurance_number'].strip() if data['insurance_number'] else None
    data['id_number'] = data['id_number'].strip() if data['id_number'] else None

    employee = Employee()
    employee.from_dict(data)
    db.session.add(employee)
    db.session.commit()
    response = jsonify(employee.to_dict())
    response.status_code = 201
    return response


