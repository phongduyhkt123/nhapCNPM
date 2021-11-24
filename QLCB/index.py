from functools import wraps

import cloudinary
from cloudinary import uploader

from QLCB import app, login
from models import *
from flask import request, render_template, redirect, session, url_for, flash
from sqlalchemy import and_
from hashlib import sha256
import base64
from flask_login import current_user, login_user
from QLCB.admin import *

@app.route('/')
def home():
    return render_template('home.html')
    #return('/admin')

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
    return redirect('/')

@app.route('/logout-employee')
def logout_employee():
    logout_user()
    return redirect('/')

@app.context_processor
def common_context():
    customer_acc = session.get('customer_acc')
    return {
        "customer_acc": customer_acc
}

# @app.route('/profile', methods=['GET', 'POST'])
# def profile():
#     return render_template('/profileEmp.html')

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
    return render_template('/profileCus.html', customer=customer, mes=mes)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug= True)