from flask import redirect, render_template, request, session
from functools import wraps
from amadeus import Client, ResponseError
from datetime import datetime
import os
import requests

get_flash_error = False
get_flash_success = False

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function






client_id_value = os.environ["CLIENT_ID"]
client_secret_value = os.environ["CLIENT_SECRET"]



amadeus = Client(
    client_id=client_id_value, 
    client_secret=client_secret_value

)
def search(city_code, checkin, checkout, adults=2, rooms=1):

    try:
        hotels_by_city = amadeus.shopping.hotel_offers.get(cityCode=city_code, checkIn=checkin, checkOut=checkout, adults=adults, roomQuantity=rooms)

        # amadeus.next(hotels_by_city)  # => returns a new response for the next page
        return hotels_by_city.data

    except ResponseError as error:

        get_flashed_error =True
        return None


def today_date():
    day = datetime.today().day
    month = datetime.today().month
    year = datetime.today().year
    date = [year, month, day]
    return date


def return_date(str_date):
    date=""
    list_date=[]
    for char in str_date:
        if char != "-":
            date += char
        else:
            list_date.append(int(date))
            date=""
    list_date.append(int(date))
    return list_date


def send_msg(email):
    url = "https://email-sender1.p.rapidapi.com/"
    
    api_key = os.environ["API_KEY"]


    querystring = {"txt_msg":"Confirmation email","to":f"{email}","from":"Explore Vacation","subject":"Confirmation message","bcc":"bcc-mail@gmail.com","reply_to":"reply-to@gmail.com","html_msg":"<html><body><b>You have booked the hotel successfully</b><br><b>Enjoy your vacation🥳 🏄</b></body></html>","cc":"cc-mail@gmail.com"}

    payload = "{\r\n    \"key1\": \"value\",\r\n    \"key2\": \"value\"\r\n}"
    headers = {
        'content-type': "application/json",
        'x-rapidapi-host': "email-sender1.p.rapidapi.com",
        'x-rapidapi-key': api_key
        }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    if response.status_code == 200:
        return 1
    else:
        return 0


