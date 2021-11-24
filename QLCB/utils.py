from datetime import datetime

from sqlalchemy import func, extract

from models import BookDetails, Tickets, Flights, TicketTypes, Airports, PaymentMethods, Customers
from QLCB import db, app
from flask_login import current_user
from hashlib import sha256

# Các năm
def report_allYear(ticketTypeID=None):
    maxDate = db.session.query(func.max(BookDetails.bookTime)).scalar()
    minDate = db.session.query(func.min(BookDetails.bookTime)).scalar()

    minYear = minDate.year if minDate else 0
    maxYear = maxDate.year if maxDate else 0

    Range = list(range(minYear, maxYear+1))

    report = dict()
    for i in Range:
        price = db.session.query(func.sum(Tickets.price)) \
            .join(BookDetails,
                  Tickets.idBookDetail == BookDetails.id) \
            .filter(extract('year', BookDetails.bookTime) == i).first()
        report[str(i)] = price[0] if price[0] else 0

    return report


# tháng trong năm
def report_monthOfYear(year):

    Range = list(range(1, 13))
    report = dict()
    for i in Range:
        price = db.session.query(func.sum(Tickets.price)) \
            .join(BookDetails,
                  Tickets.idBookDetail == BookDetails.id) \
            .filter(extract('year', BookDetails.bookTime) == year,
                    extract('month',BookDetails.bookTime) == i).first()
        report[str(i)] = price[0] if price[0] else 0

    return report


def report_quarterOfYear(year):
    Range = list(range(1, 5))
    report = dict()
    month = 1
    for i in Range:
        price = db.session.query(func.sum(Tickets.price)) \
            .join(BookDetails,
                  Tickets.idBookDetail == BookDetails.id) \
            .filter(extract('year', BookDetails.bookTime) == year,
                    extract('month', BookDetails.bookTime) >= month,
                    extract('month', BookDetails.bookTime) < month+3).first()
        report[str(i)] = price[0] if price[0] else 0
        month = month + 3

    return report

def getYear():
    query = db.session.query(BookDetails.bookTime)
    date = [row[0] for row in query.all()]
    year = set([i.year for i in date])
    return year

def get_ticket_types():
    return TicketTypes.query.all()


def get_flights(start=None, destination=None, page=None, id=None):
    flights = Flights.query
    if id:
        return flights.get(id)

    if start:
        flights = flights.filter(Flights.idStartAirport == start)
    if destination:
        flights = flights.filter(Flights.idDestinationAirport == destination)

    if page:
        size = app.config["PAGE_SIZE"]
        start = (int(page)-1)*size
        end = start + size
        return flights.all()[start:end]

    return flights.all()

def get_airports_name():
    return Airports.query.with_entities(Airports.airportName, Airports.id).all()


def count_flights():
    return Flights.query.count()


def cart_stats(cart=None):
    total_quantity, total_amount = 0, 0

    if cart:
        for p in cart.values():
            total_quantity += p["quantity"]
            total_amount += p["quantity"]*p["priceE"]

    return {
        "total_quantity": total_quantity,
        "total_amount": total_amount
    }


def add_booking(noBusinessClass, noEconomyClass, customer, employee, flight, error):
    import datetime
    bookTime = datetime.datetime.now()
    b = BookDetails(noBusinessClass=noBusinessClass, noEconomyClass=noEconomyClass,
                    bookTime=bookTime, customer=customer, employee=employee, flight=flight)
    db.session.add(b)
    try:
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        error.append(ex.args)
        return False


def add_customer(name, phone, password, error):
    password = sha256((password + phone).encode('utf-8')).hexdigest()
    customer = Customers(customerName=name, phone=phone, password=password)
    db.session.add(customer)
    try:
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        error.append(ex.args)
        return False

def get_customers(id=None):
    customers = Customers.query
    if id:
        return customers.get(id)

    return customers.all()

def edit_customer(id, name, phone, idNo, gender, address, avatar, error):
    customer = get_customers(id)
    customer.customerName = name
    customer.phone = phone
    customer.address = address
    customer.idNo = idNo
    customer.gender = gender
    customer.avatar = avatar if avatar else customer.avatar
    try:
        db.session.commit()
    except Exception as ex:
        error.append(ex.args)
        db.session.rollback()
        return False
    return True

