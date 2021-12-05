
def add_booking(noBusinessClass, noEconomyClass, customer, employee, flight, error):
    import datetime
    bookTime = datetime.datetime.now()
    pay_method = get_pay_methods(name='Tiền mặt')
    b = BookDetails(noBusinessClass=noBusinessClass, noEconomyClass=noEconomyClass,
                    bookTime=bookTime, customer=customer, employee=employee,
                    flight=flight, paymentMethod=pay_method)
    db.session.add(b)
    billAdd = False
    try:
        billAdd = True
        for i in range(0, noBusinessClass):
            t = Tickets(price=flight.priceBusinessClass, idType=1, bookDetail=b)
            db.session.add(t)
        for i in range(0, noEconomyClass):
            t = Tickets(price=flight.priceEconomyClass, idType=2, bookDetail=b)
            db.session.add(t)
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        if billAdd:
            db.session.delete(b)
            db.session.commit()
        error.append(ex.args)
        return False

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

import hmac
import json
import uuid
from datetime import datetime
from urllib.request import urlopen, Request

from pymysql import Date
from sqlalchemy import func, extract

from models import BookDetails, Tickets, Flights, TicketTypes, Airports, PaymentMethods, Customers, Stopovers, StopoverDetails
from QLCB import db, app
from flask_login import current_user
from hashlib import sha256
