from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://Siddhi:Siddhi123@cluster0.e2jmw.mongodb.net/expense")
db = client["expense_tracker"]
users_collection = db["users"]

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/all_expenses')
def all_expenses():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        user_expense_collection = db[f"expenses_{user['_id']}"]
        expenses = list(user_expense_collection.find())
        return render_template('index.html', expenses=expenses)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({"username": username, "password": hashed_password})

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register1.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Invalid username or password!', 'danger')

    return render_template('login1.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        user_expense_collection = db[f"expenses_{user['_id']}"]

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        current_year = datetime.now().year

        today_total = sum(expense['amount'] for expense in user_expense_collection.find({"date": today}))
        yesterday_total = sum(expense['amount'] for expense in user_expense_collection.find({"date": yesterday}))
        yearly_total = sum(expense['amount'] for expense in user_expense_collection.find({"date": {"$regex": f"^{current_year}"}}))
        overall_total = sum(expense['amount'] for expense in user_expense_collection.find())

        return render_template('dashboard.html', today_total=today_total, yesterday_total=yesterday_total, yearly_total=yearly_total, overall_total=overall_total)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})

        if request.method == 'POST':
            new_username = request.form.get('username')
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if new_password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('edit_profile'))

            hashed_password = generate_password_hash(new_password) if new_password else user['password']

            users_collection.update_one(
                {"_id": user['_id']},
                {"$set": {"username": new_username, "password": hashed_password}}
            )

            session['username'] = new_username
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))

        return render_template('edit_profile.html', user=user)
    return redirect(url_for('login'))

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        user_expense_collection = db[f"expenses_{user['_id']}"]

        if request.method == 'POST':
            name = request.form['name']
            category = request.form['category']
            amount = float(request.form['amount'])
            date = request.form['date']

            user_expense_collection.insert_one({
                "name": name,
                "category": category,
                "amount": amount,
                "date": date
            })
            flash("Expense added successfully!", "success")
            return redirect(url_for('dashboard'))

        return render_template('add_expense.html')
    return redirect(url_for('login'))

@app.route('/update_expense/<expense_id>', methods=['GET', 'POST'])
def update_expense(expense_id):
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        user_expense_collection = db[f"expenses_{user['_id']}"]
        expense = user_expense_collection.find_one({"_id": ObjectId(expense_id)})

        if request.method == 'POST':
            name = request.form['name']
            category = request.form['category']
            amount = float(request.form['amount'])
            date = request.form['date']

            user_expense_collection.update_one(
                {"_id": ObjectId(expense_id)},
                {"$set": {"name": name, "category": category, "amount": amount, "date": date}}
            )
            flash("Expense updated successfully!", "success")
            return redirect(url_for('dashboard'))

        return render_template('update_expense.html', expense=expense)
    return redirect(url_for('login'))

@app.route('/delete_expense/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        user_expense_collection = db[f"expenses_{user['_id']}"]

        user_expense_collection.delete_one({"_id": ObjectId(expense_id)})
        flash("Expense deleted successfully!", "success")
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
