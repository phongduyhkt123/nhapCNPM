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

# Các năm
def report_allYear():
    report = db.session.query(extract('year', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .group_by(extract('year', BookDetails.bookTime)).all()

    return report

# tháng trong năm
def report_monthOfYear(year):
    report = db.session.query(extract('month', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('month', BookDetails.bookTime)).all()

    month = []
    for i in range(1, 13):
        month.append((i, 0))
    for i in report:
        month[i[0] - 1] = i

    return month

def report_quarterOfYear(year):
    report = db.session.query(extract('quarter', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('quarter', BookDetails.bookTime)).all()

    quarter = [(1, 0), (2, 0), (3, 0), (4, 0)]
    for i in report:
        quarter[i[0] - 1] = i

    return quarter

def report_tickets_year():
    report = db.session.query(extract('year', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .group_by(extract('year', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('year', BookDetails.bookTime), Tickets.idType).all()

    return report

def report_tickets_months(year):
    report = db.session.query(extract('month', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('month', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('month', BookDetails.bookTime), Tickets.idType).all()

    return report

def report_tickets_quarter(year):
    report = db.session.query(extract('quarter', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('quarter', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('quarter', BookDetails.bookTime), Tickets.idType).all()

    return report

def getYear():
    query = db.session.query(BookDetails.bookTime)
    date = [row[0] for row in query.all()]
    year = set([i.year for i in date])
    return year

def get_ticket_types():
    return TicketTypes.query.all()

def get_flights(start=None, destination=None, page=None, id=None, flew=False):
    flights = Flights.query
    if id:
        return flights.get(id)

    if not flew:
        today = Date.today()
        flights = flights.filter(Flights.takeOffTime > today)
    if start:
        flights = flights.filter(Flights.idStartAirport == start)
    if destination:
        flights = flights.filter(Flights.idDestinationAirport == destination)

    if page:
        size = app.config["PAGE_SIZE"]
        start = (int(page)-1)*size
        end = start + size
        return flights.all()[start:end], len(flights.all())

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

# region payMomo
def payByMomo(totalPrice, url):
    domain =  'http://127.0.0.1:5000/'
    endpoint = "https://test-payment.momo.vn/gw_payment/transactionProcessor"
    partnerCode = "MOMO544Q20211126"
    accessKey = "FoblaCbnWl9gdHeg"
    serectkey = "8QCHW2eoJJWhZU6TJp0L2dKlngawMaP8"
    orderInfo = "Thanh toán vé máy bay "
    returnUrl = url
    notifyurl = domain + ''
    amount = totalPrice
    orderId = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    requestType = "captureMoMoWallet"
    extraData = "merchantName=;merchantId="  # pass empty value if your merchant does not have stores else merchantName=[storeName]; merchantId=[storeId] to identify a transaction map with a physical store
    # before sign HMAC SHA256 with format
    # partnerCode=$partnerCode&accessKey=$accessKey&requestId=$requestId&amount=$amount&orderId=$oderId&orderInfo=$orderInfo&returnUrl=$returnUrl&notifyUrl=$notifyUrl&extraData=$extraData
    rawSignature = "partnerCode=" + partnerCode + "&accessKey=" + accessKey + "&requestId=" + requestId + "&amount=" + amount + "&orderId=" + orderId + "&orderInfo=" + orderInfo + "&returnUrl=" + returnUrl + "&notifyUrl=" + notifyurl + "&extraData=" + extraData
    h = hmac.new(bytes(serectkey, 'utf-8'), rawSignature.encode('utf8'), sha256)
    signature = h.hexdigest()
    data = {
        'partnerCode': partnerCode,
        'accessKey': accessKey,
        'requestId': requestId,
        'amount': amount,
        'orderId': orderId,
        'orderInfo': orderInfo,
        'returnUrl': returnUrl,
        'notifyUrl': notifyurl,
        'extraData': extraData,
        'requestType': requestType,
        'signature': signature
    }
    data = json.dumps(data).encode('utf-8')
    clen = len(data)
    req = Request(endpoint, data, {'Content-Type': 'application/json', 'Content-Length': clen})
    f = urlopen(req)
    response = f.read()
    f.close()
    import pdb
    pdb.set_trace()
    return json.loads(response)['payUrl']


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
        return customers.get(int(id))

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

def get_pay_methods(name=None):
    pm = PaymentMethods.query
    if name:
        return pm.filter(PaymentMethods.PMethodName == name).first()
    return pm.all()

def get_book_detail(id):
    return BookDetails.query.get(id)

def get_stopover_detail(fid = None):
    sd = StopoverDetails.query
    if fid:
        sd = sd.filter(StopoverDetails.idFlight == fid)

    return sd.all()


def get_tickets(cid=None):
    tickets = Tickets.query
    if cid:
        tickets = tickets.filter(Tickets.id)

def get_slot_remain(fid):
    b, e = db.session.query(func.sum(BookDetails.noBusinessClass),
                         func.sum(BookDetails.noEconomyClass)).filter(
        BookDetails.idFlight == fid).one()
    return {
        "economy": e if e else 0,
        "business": b if b else 0
    }

