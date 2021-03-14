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

@bp.route('/employees')
def get_employees():
    employees = Employee.query.all()
    res = [item.to_dict() for item in employees]
    return jsonify(res)

@bp.route('/employee/<int:emp_id>')
def get_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
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


@bp.route('/employee', methods=['POST'])
def add_employee():
    data = {}
    if not request.form['fullname']  or not request.form['title'] or not request.form['is_profile_pic']:
        return bad_request('Must include Full Name & Title')
    else:
        data['fullname'] = request.form['fullname'] .strip()
        data['title'] = request.form['title'].strip()

    
    data['address'] = request.form['address'].strip() if request.form['address'] else None
    data['fixed_salary'] = int(request.form['fixed_salary']) if request.form['fixed_salary'] else None
    data['variable_salary'] = int(request.form['variable_salary']) if request.form['variable_salary'] else None
    if request.form['employment_date']:
        data['employment_date'] = datetime.strptime(request.form['employment_date'], '%Y-%m-%d')
    data['phone'] = request.form['phone'].strip() if request.form['phone'] else None
    data['insurance_number'] = request.form['insurance_number'].strip() if request.form['insurance_number'] else None
    data['id_number'] = request.form['id_number'].strip() if request.form['id_number'] else None

    employee = Employee()
    employee.from_dict(data)
    db.session.add(employee)
    db.session.commit()
    response = jsonify(employee.to_dict())
    response.status_code = 201
    return response


