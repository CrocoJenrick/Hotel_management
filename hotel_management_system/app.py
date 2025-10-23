from flask import Flask, render_template, request, redirect, url_for, session 
import MySQLdb
from db_config import get_db_connection 

# This secret key is a crucial security measure used for various purposes
app = Flask (__name__)
app.secret_key = "your_secret_key" 

# LOGIN page
@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session ["loggedin"] = True
            session ["username"] = user[1]
            return redirect(url_for("dashboard"))
        else: 
            msg = "Invalid username or password"
    return render_template("login.html", msg=msg)

#eto pala ung logout
@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("username", None)
    return redirect(url_for("login"))

#Logout nlng talga hapdi at kirot ang sakit
@app.route("/dashboard")
def dashboard():
    if "loggedin" in session:
        return render_template("dashboard.html", username=session["username"])
    else: 
        return redirect(url_for("login"))
    
#Customer registration 
@app.route("/register_customer", methods=["GET", "POST"])
def register_customer():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    msg = ""
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]

        conn = get_db_connection()
        cur = conn.cursor()
         # Check if customer already exists by name, phone, or email
        cur.execute(
            "SELECT * FROM customers WHERE name = %s OR phone = %s OR email = %s",
            (name, phone, email),
        )
        existing_customer = cur.fetchone()

        if existing_customer:
            # Update the existing record
            cur.execute(
                "UPDATE customers SET name = %s, phone = %s, email = %s WHERE id = %s ",
                (name, phone, email, existing_customer[0]),
            )
            conn.commit()
            msg = "Customer details updated successfully."
        else:
            # Insert a new record
            cur.execute(
                "INSERT INTO customers (name, phone, email) VALUES (%s, %s, %s)",
                (name, phone, email),
            )
            conn.commit()

        conn.commit()
        cur.close()
        conn.close()
        msg = "Customer registered successfully!!!!!!!!!"
        
    return render_template("register_customer.html", msg=msg)

#customer view
@app.route("/view_customers")
def view_customers():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("view_customers.html", customers=customers)

#customers updates
@app.route("/edit_customer/<int:id>", methods=["GET", "POST"])
def edit_customer(id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]

        cur.execute("UPDATE customers SET name=%s, phone=%s, email=%s WHERE id=%s", (name, phone, email, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("view_customers"))

    cur.execute("SELECT * FROM customers WHERE id=%s", (id,))
    customer = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("edit_customer.html", customer=customer)

#customer delete
@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("view_customers"))

#Bookings in the room 
@app.route("/booking", methods=["GET","POST"])
def booking():
    if "loggedin" not in session:
        return redirect(url_for("login"))
    
    msg = ""
    conn = get_db_connection()
    cur = conn.cursor()

    #Get all the rows 
    cur.execute("SELECT id, name FROM customers")
    customers = cur.fetchall()

    cur.execute("SELECT id, room_number FROM rooms")
    rooms = cur.fetchall()

    if request.method == "POST":

        #Get form data
        customer_id = request.form["customer_id"]
        room_id = request.form["room_id"]
        checkin = request.form ["checkin_date"]
        checkout = request.form ["checkout_date"]
        total = request.form ["total_amount"]

        #insert bookings 
        cur.execute(
            "INSERT INTO bookings (customer_id, room_id, checkin_date, checkout_date, total_amount) VALUES (%s,%s,%s,%s,%s)",
            (customer_id, room_id, checkin, checkout, total)
        )
        conn.commit()
        msg = "OKAY NA BOOK KA NA GAGO!!!"

    cur.close()
    conn.close()

    return render_template("booking.html", customers=customers, rooms=rooms, msg=msg)

    
if __name__ == "__main__":
    app.run(debug=True)