from flask import Flask, render_template, request, redirect, url_for, session
import csv
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for sessions

# Menu & Resources
MENU = {
    "americano": {"ingredients": {"water": 50, "coffee": 18}, "cost": 90},
    "latte": {"ingredients": {"water": 200, "milk": 150, "coffee": 24}, "cost": 120},
    "cappuccino": {"ingredients": {"water": 250, "milk": 100, "coffee": 24}, "cost": 110}
}

resources = {"water": 900, "milk": 700, "coffee": 400}
profit = 0

ADMIN_USERNAME = "DrKamaldeep"
ADMIN_PASSWORD = "12345"

# Utility functions
def is_resources_sufficient(order_ingredients):
    for item in order_ingredients:
        if order_ingredients[item] > resources.get(item, 0):
            return False, f"Sorry, not enough {item}."
    return True, ""

def is_transaction_successful(money_received, drink_cost):
    global profit
    if money_received >= drink_cost:
        change = money_received - drink_cost
        profit += drink_cost
        return True, change
    else:
        return False, "Not enough money. Refunded."

def make_coffee(drink_name, order_ingredients):
    for item in order_ingredients:
        resources[item] -= order_ingredients[item]

def log_transaction(drink, amount_paid, change):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("transactions.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([now, drink, amount_paid, change])

# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    if request.method == "POST":
        drink_choice = request.form["drink"]
        total_money = sum(int(request.form.get(note, 0)) * int(note) for note in ["10", "20", "50", "100", "200", "500"])

        drink = MENU.get(drink_choice)
        if drink:
            ok, msg = is_resources_sufficient(drink["ingredients"])
            if not ok:
                message = msg
            else:
                success, result = is_transaction_successful(total_money, drink["cost"])
                if success:
                    make_coffee(drink_choice, drink["ingredients"])
                    log_transaction(drink_choice, total_money, result)
                    message = f"Here is your {drink_choice} ☕. Change: ₹{result}"
                else:
                    message = result
        else:
            message = "Invalid drink selected."

        return render_template("result.html", message=message)

    return render_template("index.html", menu=MENU)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("admin_login.html", error="Invalid credentials.")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    transactions = []
    try:
        with open("transactions.csv", newline="") as file:
            reader = csv.reader(file)
            transactions = list(reader)
    except FileNotFoundError:
        transactions = []

    return render_template("admin_dashboard.html", resources=resources, profit=profit, transactions=transactions)

@app.route("/logout")
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
