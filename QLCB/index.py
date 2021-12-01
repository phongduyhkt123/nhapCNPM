import math
from functools import wraps

import cloudinary
from cloudinary import uploader

from QLCB import app, login
from models import *
from flask import request, render_template, redirect, session, url_for, flash
from sqlalchemy import and_
from hashlib import sha256
import base64
from flask_login import current_user, login_user, login_required
from QLCB.admin import *

@app.route('/customer')
def homeCus():
    return render_template('homeCus.html')

@app.route('/employee')
def homeEmp():
    return render_template('homeEmp.html')

@login.user_loader
def load_usr(id):
    return Employees.query.get(int(id))

def login_customer_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if not session.get('customer_acc'):
            return redirect(url_for('login_customer', next=request.url))
        return f(*args, **kwargs)
    return check

def login_employee_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_employee', next=request.url))
        return f(*args, **kwargs)
    return check

@app.route('/login-admin', methods=['post'])
def login():
    if not current_user.is_authenticated:
        username = request.form.get('username')
        password = request.form.get('password')
        password = sha256((password + username).encode('utf-8')).hexdigest()
        admin_user = db.session.query(Employees).join(Roles).filter(and_(
            Employees.username == username,
            Employees.password == password,
            Roles.roleName == 'Admin')).first()
        if admin_user:
            login_user(admin_user)
        else:
            flash('Login failed', 'error')
    return redirect('/admin')

@app.route('/login-employee', methods=['post', 'get'])
def login_employee():
    if not current_user.is_authenticated :
        if request.method == 'GET':
            return render_template('employee/login.html')
        username = request.form.get('username')
        password = request.form.get('password')
        password = sha256((password + username).encode('utf-8')).hexdigest()
        employee_user = db.session.query(Employees).join(Roles).filter(and_(
            Employees.username == username,
            Employees.password == password)).first()
        if employee_user:
            login_user(employee_user)
        else:
            return 'login failed!'
    return redirect(request.args.get('next') if request.args.get('next') else '/employee')


@app.route('/login', methods=['get', 'post'])
def login_customer():
    error = ""
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        password = sha256((password + phone).encode('utf-8')).hexdigest()
        user = db.session.query(Customers).filter(and_(
            Customers.phone == phone,
            Customers.password == password)).first()
        if user: # nếu đăng nhập thành công
            session['customer_acc'] = {
                "id": user.id,
                "customerName": user.customerName,
            }
            return redirect(request.args.get('next', '/'))
        else:
            error = "Login failed!"
    else:
        if session.get('customer_acc'):
            return redirect('/')
    return render_template('/login.html', error=error)

@app.route('/signup', methods=['post'])
def signup():
    error = []
    data = request.form.copy()
    del data['repassword']
    try:
        if utils.add_customer(**data, error=error):
            return redirect(url_for('login_customer'))
    except Exception as ex:
        error.append(ex.args)
    return render_template('/login.html', isSignup=1, err=error[0][0])

@app.route('/logout')
def logout_customer():
    session['customer_acc'] = None
    return redirect('/customer')

@app.route('/logout-employee')
def logout_employee():
    logout_user()
    return redirect('/employee')

@app.context_processor
def common_context():
    customer_acc = session.get('customer_acc')
    return {
        "customer_acc": customer_acc
}

@app.route('/manage-flight-list', methods=['post', 'get'])
def manage_flight_list():
    flights = utils.get_flights(start=int(request.form.get("start", 0)),
                                destination=int(request.form.get("destination", 0)),
                                page=request.args.get("page", 1))
    slots = {}
    for f in flights[0]:
        slots[f.id] = utils.get_slot_remain(f.id)

    page_num = math.ceil(flights[1] / app.config["PAGE_SIZE"])
    airport_name = utils.get_airports_name()

    return render_template('flight-list.html',
                           airport_name=airport_name,
                           flights=flights[0],
                           date_rule=app.config["MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF"],
                           page_num=page_num,
                           isEmp=True,
                           slots=slots)

@app.route('/flight-list', methods=['post', 'get'])
def show_flight():
    flights = utils.get_flights(start=int(request.form.get("start", 0)),
                                destination=int(request.form.get("destination", 0)),
                                page=request.args.get("page", 1))
    slots = {}
    for f in flights[0]:
        slots[f.id] = utils.get_slot_remain(f.id)

    page_num = math.ceil(flights[1] / app.config["PAGE_SIZE"])
    airport_name = utils.get_airports_name()

    return render_template('flight-list.html',
                           airport_name=airport_name,
                           flights=flights[0],
                           date_rule=app.config["MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF"],
                           page_num=page_num,
                           slots=slots)

@app.route('/manage-flight-route')
@login_required
def route():
    fr = Flights.query.all()
    list_route = []

    for i in fr:
        name1 = Airports.query.add_columns(Airports.airportName).filter(i.idStartAirport == Airports.id).one()
        name2 = Airports.query.add_columns(Airports.airportName).filter(i.idDestinationAirport == Airports.id).one()
        dic = {
            'id': i.id,
            'name1': name1[1],
            'name2': name2[1],
            'takeOffTime': i.takeOffTime,
            'noBusinessClass': i.noBusinessClass,
            'priceBusinessClass': i.priceBusinessClass,
            'noEconomyClass': i.noEconomyClass,
            'priceEconomyClass': i.priceEconomyClass
        }
        list_route.append(dic)
    #print(list_route)

    return render_template('/manage-flight-route.html', list_route=list_route)

@app.route('/booking/<fid>', methods=['GET', 'POST'])
@login_employee_required
def book(fid):
    flight = utils.get_flights(id=fid)
    customers = utils.get_customers()
    error = []
    msg = None
    if request.method == 'POST':
        no_business = int(request.form.get('noBusiness'))
        no_economy = int(request.form.get('noEconomy'))
        employee = current_user
        customer = utils.get_customers(request.form.get('cid'))
        if utils.add_booking(noEconomyClass=no_economy, noBusinessClass=no_business,
                             customer=customer, employee=employee, flight=flight, error=error):
            msg = "Booking Successful!"

    slot = utils.get_slot_remain(fid=flight.id)
    return render_template('booking.html',
                           customers=customers,
                           flight=flight,
                           slot=slot,
                           isEmp=True,
                           error=error,
                           msg=msg)

@app.route('/manage-flight/<id>')
def schedule_employee(id):
    flight = utils.get_flights(id=id)
    slot = utils.get_slot_remain(id)
    stopovers = utils.get_stopover_detail(fid=id)
    return render_template('schedule.html',
                           flight=flight,
                           slot=slot,
                           isEmp=True,
                           stopovers=stopovers)

@app.route('/flight-detail/<id>')
def schedule_customer(id):
    flight = utils.get_flights(id=id)
    slot = utils.get_slot_remain(id)
    stopovers = utils.get_stopover_detail(fid=id)
    return render_template('schedule.html',
                           flight=flight,
                           slot=slot,
                           stopovers=stopovers)

@app.route('/bookingOnline/<fid>', methods=['GET', 'POST'])
@login_customer_required
def book_online(fid):
    flight = utils.get_flights(id=fid)
    error = []
    msg = None

    if request.method == 'POST':
        amount = request.form.get('total')
        try:
            a = utils.payByMomo(str(amount), request.url)
            return redirect(a)
        except Exception as ex:
            print(ex.args)
            error.append("Something wrong! Please try again!")

    # no_business = int(request.form.get('noBusiness'))
    # no_economy = int(request.form.get('noEconomy'))
    # employee = current_user
    # customer = utils.get_customers(id=session.get('customer_acc')['id'])
    # if utils.add_booking(noEconomyClass=no_economy, noBusinessClass=no_business,
    #                      customer=customer, employee=employee, flight=flight, error=error):
    #     msg = "Booking Successful!"
    slot = utils.get_slot_remain(fid)
    return render_template('booking.html',
                           flight=flight,
                           slot=slot,
                           error=error,
                           msg=msg)


@app.route('/changePw', methods=['GET', 'POST'])
@login_required
def change_password():
     return render_template('/changePw.html')

@app.route('/profileEmp', methods=['post', 'get'])
@login_employee_required
def edit_employee_profit():
    mes = []
    if request.method == 'POST':
        pass
    return render_template('/profileEmp.html',isEmp=True,mes=mes)

@app.route('/profile', methods=['post', 'get'])
@login_customer_required
def edit_customer_profit():
    customer_acc = session['customer_acc']
    id = customer_acc['id']
    mes = []
    if request.method == 'POST':
        data = request.form.copy()
        avatar = request.files['avatar']
        if avatar:
            info = cloudinary.uploader.upload(avatar)
            data['avatar'] = info['secure_url']
        else:
            data['avatar'] = None
        if utils.edit_customer(id, **data, error=mes):
            return redirect(url_for('edit_customer_profit'))
        else:
            if data['avatar']:
                cloudinary.uploader.destroy(info['public_id'])
    customer = utils.get_customers(id)
    return render_template('/profile.html', customer=customer, mes=mes)

@app.errorhandler(404)
def not_found(e):
    return render_template('/404.html')

if __name__ == '__main__':
    app.run(debug= True)