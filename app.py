import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime
import sqlite3 as sql
from helpers import login_required, search, get_flash_error, today_date, return_date, send_msg, get_flash_success

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    else:
        data=[]
        city_code=request.form.get("city")
        checkin=request.form.get("checkin")
        checkout=request.form.get("checkout")
        adults=request.form.get("adults")
        rooms=request.form.get("rooms")

        # date validity
        in_date = return_date(checkin)
        out_date= return_date(checkout)
        todayDate = today_date()

        if in_date[0] < todayDate[0] or in_date[1] < todayDate[1] or in_date[2] <= todayDate[2] or out_date[0] != in_date[0] or out_date[1] != in_date[1] or out_date[2] <= in_date[2]:
            return render_template("index.html",get_flash_error=True ,msg="Please select a valid date")
        else:
            duration = out_date[2] - in_date[2]

        if adults == "Choose...":
            adults = None


        if rooms =="Choose...":
            rooms = None



        
        if not rooms and not adults:
            data = search(city_code=city_code, checkin=checkin, checkout=checkout)
            rooms=1
            adults=2
        elif not rooms:
            data = search(city_code=city_code, checkin=checkin, checkout=checkout, adults=adults)
            rooms=1

        elif not adults:
            data = search(city_code=city_code, checkin=checkin, checkout=checkout, rooms=rooms)
            adults=2
        else:
            data = search(city_code=city_code, checkin=checkin, checkout=checkout, adults=adults, rooms=rooms)
        if not data:
            
            return render_template("index.html",get_flash_error=True ,msg="Invalid input data")
        else:
            data_list=[]
            data_dict={}
            for element in data:
                # itererating through each hotal with its offers
                data_dict={}
                # for hotel
                hotel_id = element["hotel"]["hotelId"]
                hotel_name = element["hotel"]["name"]

                if "rating" in element["hotel"]:
                    rating = int(element["hotel"]["rating"])
                else:
                    rating = None

                # offers in this hotel
                price = element["offers"][0]["price"]["total"]
                currency = element["offers"][0]["price"]["currency"]
                data_dict={
                    "hotel_id":hotel_id,
                    "hotel_name":hotel_name,
                    "rating":rating,
                    "price": price,
                    "currency":currency,
                    "days":duration,
                    "adults":adults,
                    "rooms":rooms
                }

                data_list.append(data_dict)

            session["data"]=data
            session["data_list"]=data_list

            return redirect("/offers")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    if session.get("cost") is None:
        session.clear()


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "GET":
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("login.html")
    else:

        # Query database for username
        con = sql.connect("user.db")
        cur = con.cursor()
        namee= request.form.get("username")
        cur.execute("SELECT * FROM users WHERE user_name = (?)", (namee,))

        rows = cur.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][3], request.form.get("password")):
            get_flash_error=True
            msg="Invalid username and/or password"
            return render_template("login.html", get_flash_error=get_flash_error, msg=msg)



        session["user_id"] = rows[0][0]
        if session.get("cost") is None:
            # Redirect user to home page
            return redirect("/")
        else:
            return redirect("/payment")




@app.route("/register", methods =["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    else:
        email = request.form.get("email")
        name = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")
        con = sql.connect("user.db")
        cur = con.cursor()
        cur.execute("SELECT user_name FROM users")

        names = cur.fetchall()
        for row in names:
            if row == name:
                get_flash_error=True
                msg="This user name is token"
                return render_template("register.html", get_flash_error=get_flash_error, msg=msg)


        if password != confirm_password :
            get_flash_error=True
            msg="Password doesn't match"
            return render_template("register.html", get_flash_error=get_flash_error, msg=msg)
        else:
            con = sql.connect("user.db")
            cur = con.cursor()
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            cur.execute("INSERT INTO users (user_name, email, hash) VALUES (?,?, ?)", (name, email, hashed_password))
            con.commit()

            # Remember which user has logged in
            cur.execute("SELECT id FROM users WHERE user_name =(?)",(name,))
            session["user_id"]  = cur.fetchall()
            return redirect("/")


@app.route("/view", methods=["GET","POST"])
def view():
    if request.method == "GET":

        # address
        adr_line = session["selected_offer"]["hotel"]["address"]["lines"][0]
        city = session["selected_offer"]["hotel"]["address"]["cityName"]
        address=adr_line.title() +" - "+ city.title()
        session["selected_data_dict"]["address"]= address

        # contact
        contact_info = {}
        for contact in ["phone", "fax", "email"]:
            if "contact" in session["selected_offer"]["hotel"]:
                if contact in session["selected_offer"]["hotel"]["contact"]:
                    contact_info[contact]= session["selected_offer"]["hotel"]["contact"][contact]
            session["selected_data_dict"]["contact"]= contact_info

        # discribtion -> some text
        if "description" in session["selected_offer"]["hotel"]:
            description_str = session["selected_offer"]["hotel"]["description"]["text"]
            description_list = description_str.split(sep=".", maxsplit=1)
            session["selected_data_dict"]["description"] = description_list

        # amenities
        amen=[]
        if "amenities" in session["selected_offer"]["hotel"]:
            amen = session["selected_offer"]["hotel"]["amenities"]
            session["selected_data_dict"]["amenities"] = amen

        # room
        if "beds" in session["selected_offer"]["offers"][0]["room"]["typeEstimated"]:
            room ={}
            if "category" in session["selected_offer"]["offers"][0]["room"]["typeEstimated"]:
                room["category"] = session["selected_offer"]["offers"][0]["room"]["typeEstimated"]["category"]
            if "beds" in session["selected_offer"]["offers"][0]["room"]["typeEstimated"]:
                room["Beds"] = session["selected_offer"]["offers"][0]["room"]["typeEstimated"]["beds"]
            if "bedType" in session["selected_offer"]["offers"][0]["room"]["typeEstimated"]:
                room["Bed_type"] = session["selected_offer"]["offers"][0]["room"]["typeEstimated"]["bedType"]

            session["selected_data_dict"]["room"]=room

            if "description" in session["selected_offer"]["offers"][0]["room"]:
                session["selected_data_dict"]["description"] = session["selected_offer"]["offers"][0]["room"]["description"]["text"]

        return render_template("view.html", data_dict=session["selected_data_dict"])
        # return render_template("view.html")
    else:
        session["cost"] = session["selected_data_dict"]["price"]
        return redirect("/payment")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/offers",methods=["POST","GET"])
def offers():
    if request.method == "GET":
        return render_template("offers.html",data_list=session["data_list"])
    else:
        # steps:
        # extract data of selected hotel then put it in session["selected_offer"]
        # from datalist get data of selected hotel put it in session["selected_data_dict"]
        # redirect to /view
        # in /views use session["selected hotel"] to fill in view.html page by -> render_template("view.html", selected_offer=session["selected_offer"])

        hotel_id=request.form.get("hotel_id")
        for element in session["data"]:
            if element["hotel"]["hotelId"] == hotel_id:
                session["selected_offer"]=element
                print(session["selected_offer"])
                break
        for element in session["data_list"]:
            if element["hotel_id"]== hotel_id:
                session["selected_data_dict"]=element
                print(session["selected_data_dict"])
                break
        return redirect("/view")


@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    if request.method == "GET":
        return render_template("payment.html")
    else:
        con = sql.connect("user.db")
        cur = con.cursor()
        cur.execute("SELECT email FROM users WHERE id = (?)", (session["user_id"],))
        user_email = cur.fetchall()

        if not user_email or not send_msg(user_email[0]["email"]):
            get_flash_error=True
            msg="failed send confirmation message"
            return render_template("offers.html", get_flash_error=get_flash_error, msg=msg)

        else:
            get_flash_success = True
            msg="Confirmation Email sent successfully"
            return render_template("offers.html", data_list=session["data_list"], get_flash_success=get_flash_success, msg=msg)
        return redirect("/offers")
        

