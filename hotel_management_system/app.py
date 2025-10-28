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

#Dashboard
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
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    msg = ""
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        action = request.form.get("_action")

        try:
            # ADD NEW BOOKING
            if action == "add":
                customer_id = request.form["customer_id"]
                room_id = request.form["room_id"]
                checkin = request.form["checkin_date"]
                checkout = request.form["checkout_date"]
                total = request.form["total_amount"]

                cur.execute(
                    "SELECT id FROM bookings WHERE room_id=%s AND checkin_date=%s AND checkout_date=%s",
                    (room_id, checkin, checkout),
                )
                existing = cur.fetchone()

                if existing:
                    msg = "Booking already exists for this room and date."
                else:
                    cur.execute(
                        "INSERT INTO bookings (customer_id, room_id, checkin_date, checkout_date, total_amount) VALUES (%s, %s, %s, %s, %s)",
                        (customer_id, room_id, checkin, checkout, total),
                    )
                    cur.execute("UPDATE rooms SET status='Occupied' WHERE id=%s", (room_id,))
                    conn.commit()
                    msg = "Booking added successfully."

            # UPDATE EXISTING BOOKING
            elif action == "update":
                booking_id = request.form["id"]
                customer_id = request.form["customer_id"]
                room_id = request.form["room_id"]
                checkin = request.form["checkin_date"]
                checkout = request.form["checkout_date"]
                total = request.form["total_amount"]

                cur.execute(
                    "UPDATE bookings SET customer_id=%s, room_id=%s, checkin_date=%s, checkout_date=%s, total_amount=%s WHERE id=%s",
                    (customer_id, room_id, checkin, checkout, total, booking_id),
                )
                conn.commit()
                msg = "Booking updated successfully."

            # DELETE BOOKING
            elif action == "delete":
                booking_id = request.form["id"]

                # Get room_id before deleting
                cur.execute("SELECT room_id FROM bookings WHERE id=%s", (booking_id,))
                room = cur.fetchone()

                # Delete booking
                cur.execute("DELETE FROM bookings WHERE id=%s", (booking_id,))
                conn.commit()

                # Update room status to 'Available'
                if room:
                    cur.execute("UPDATE rooms SET status='Available' WHERE id=%s", (room[0],))
                    conn.commit()

                msg = "Booking deleted successfully."

        except Exception as e:
            msg = f"Error processing booking: {e}"

    # Fetch customers, rooms, and bookings for display
    cur.execute("SELECT id, name FROM customers")
    customers = cur.fetchall()
    cur.execute("SELECT id, room_number FROM rooms")
    rooms = cur.fetchall()
    cur.execute(
        "SELECT b.id, c.name, r.room_number, b.checkin_date, b.checkout_date, b.total_amount FROM bookings b JOIN customers c ON b.customer_id=c.id JOIN rooms r ON b.room_id=r.id ORDER BY b.id ASC"
    )
    bookings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("booking.html", customers=customers, rooms=rooms, bookings=bookings, msg=msg)


@app.route("/room_info", methods=["GET", "POST"])
def room_info():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    msg = ""

    # --- Auto update room status based on bookings ---
    try:
        # 1. Mark rooms as occupied if they have active bookings
        cur.execute("""
            UPDATE rooms 
            SET status = 'Occupied'
            WHERE id IN (
                SELECT room_id FROM bookings
                WHERE CURDATE() BETWEEN checkin_date AND checkout_date
            )
        """)

        # 2. Mark rooms as available if their bookings ended
        cur.execute("""
            UPDATE rooms 
            SET status = 'Available'
            WHERE id NOT IN (
                SELECT room_id FROM bookings
                WHERE CURDATE() BETWEEN checkin_date AND checkout_date
            )
            AND status != 'Maintenance'
        """)

        conn.commit()
    except Exception as e:
        msg = f"Auto-update error: {e}"

    # --- Handle manual actions (Add, Delete, Update) ---
    if request.method == "POST":
        try:
            delete_id = request.form.get("delete_id")
            update_id = request.form.get("update_id")
            new_status = request.form.get("new_status")

            if delete_id:
                cur.execute("DELETE FROM rooms WHERE id=%s", (delete_id,))
                msg = "Room deleted successfully."
            elif update_id and new_status:
                cur.execute("UPDATE rooms SET status=%s WHERE id=%s", (new_status, update_id))
                msg = f"Room status updated to {new_status}."
            else:
                room_number = request.form["room_number"]
                room_type = request.form["room_type"]
                price = request.form["price"]
                status = request.form["status"]
                cur.execute(
                    "INSERT INTO rooms (room_number, room_type, price, status) VALUES (%s, %s, %s, %s)",
                    (room_number, room_type, price, status),
                )
                msg = "Room added successfully."
            conn.commit()
        except Exception as e:
            msg = f"Error processing request: {e}"

    # --- Fetch updated room data ---
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rooms WHERE status='Occupied'")
    occupied_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "room_info.html",
        rooms=rooms,
        msg=msg,
        total_rooms=total_rooms,
        occupied_count=occupied_count
    )


if __name__ == "__main__":
    app.run(debug=True)