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
    session.pop("logggedin", None)
    session.pop("username", None)
    return redirect(url_for("login"))

#Logout nlng talga hapdi at kirot ang sakit
@app.route("/dashboard")
def dashboard():
    if "loggedin" in session:
        return render_template("dashboard.html", username=session["username"])
    else: 
        return redirect(url_for("login"))
    
if __name__ == "__main__":
    app.run(debug=True)