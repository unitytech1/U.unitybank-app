import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from collections import defaultdict
from flask_login import logout_user

def generate_reference():
    return "UB-" + str(random.randint(100000,999999)) + "-TRF"

app = Flask(__name__)
app.secret_key = 'unity_bank_key_2026'

# CONFIG
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unity_bank.db'
app.config['SESSION_COOKIE_SECURE']= False
app.config['REMEMBER_COOKIE_SECURE']= False

# Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# EMAIL CONFIG
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('UnityBank', 'j99310482@gmail.com')  

# INIT
db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =========================
# MODELS
# =========================

class User(db.Model, UserMixin):
    transfer_pin = db.Column(db.String(10))
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    balance = db.Column(db.Float, default=25000000.0)
    profile_pic_path = db.Column(db.String(255), nullable=True)

    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    transactions = db.relationship('Transaction', backref='sender', lazy=True)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_name = db.Column(db.String(100))
    account_number = db.Column(db.String(20))
    amount = db.Column(db.Float)

    transaction_type = db.Column(db.String(10))  # debit / credit
    date = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# FAKE TRANSACTION GENERATOR
# =========================

def generate_fake_transactions(user):
    names = [
        "John Smith", "Emily Johnson", "Michael Williams",
        "Christopher Brown", "Jessica Davis", "Daniel Miller",
        "Liam Noah","Oliver Theodore"," James Henrry","Mateo Eijah",
        "Lucas William","Benjamin Levi","Sebastian Jack","Ethan Asher"
        "Sarah Wilson", "David Anderson", "Laura Thomas", "James Taylor"
    ]

    banks = [
        "Chase Bank", "Bank of America", "Wells Fargo",
        "Citibank", "U.S. Bank", "PNC Bank",
        "M&T Bank Corp","KeyCorp(KeyBank)","State Street Corp",
        "Capital One", "TD Bank", "Truist Bank","Morgan Stanley"
    ]

    start_date = datetime(2015, 1, 1)
    end_date = datetime(2025, 1, 1)

    transactions = []
    balance = 0

    for _ in range(199):  # leave space for last adjustment
        random_date = start_date + (end_date - start_date) * random.random()
        t_type = random.choice(['debit', 'credit'])
        amount = round(random.uniform(1000, 50000), 2)

        if t_type == 'credit':
            balance += amount
        else:
            balance -= amount

        transaction = Transaction(
            sender_id=user.id,
            receiver_name=f"{random.choice(names)} ({random.choice(banks)})",
            account_number=str(random.randint(100000000, 999999999)),
            amount=amount,
            transaction_type=t_type,
            date=random_date
        )

        transactions.append(transaction)

    # 🎯 FINAL ADJUSTMENT TO HIT EXACT BALANCE
    target_balance = 25000000.00
    difference = target_balance - balance

    final_transaction = Transaction(
        sender_id=user.id,
        receiver_name="Final Adjustment (System)",
        account_number="000000000",
        amount=abs(difference),
        transaction_type='credit' if difference > 0 else 'debit',
        date=end_date
    )

    transactions.append(final_transaction)

    # ✅ SET USER BALANCE EXACTLY
    user.balance = target_balance

    db.session.add_all(transactions)
    db.session.commit()
 
# =========================
# OPTIONAL: RANDOM CREDIT
# =========================

def add_random_credit(user):
    sources = [
        "Amazon Payroll", "Apple Inc.", "Google LLC",
        "Stripe Payments", "PayPal", "Employer Deposit"
    ]

    banks = ["Chase Bank", "Bank of America", "Wells Fargo"]

    transaction = Transaction(
        sender_id=user.id,
        receiver_name=f"{random.choice(sources)} ({random.choice(banks)})",
        account_number=str(random.randint(100000000, 999999999)),
        amount=round(random.uniform(500, 5000), 2),
        transaction_type='credit',
        date=datetime.utcnow()
    )

    db.session.add(transaction)
    db.session.commit()


# =========================
# LOGIN MANAGER
# =========================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE DB
with app.app_context():
    db.create_all()


# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/invest')
def invest():
    return render_template(
        'invest.html',
        investment_balance=12450,
        investments=[
            {"name":"Apple","type":"Stocks","amount":129.89,"growth":"+3.5%"},
            {"name":"Bitcoin","type":"Crypto","amount":210.93,"growth":"+1.2%"},
            {"name":"Tesla","type":"Stocks","amount":300.45,"growth":"+4.1%"},
            {"name":"Ethereum","type":"Crypto","amount":180.22,"growth":"+2.3%"},
            {"name":"Index Fund","type":"Fund","amount":500.00,"growth":"+5.0%"},
            {"name":"Real Estate","type":"Property","amount":1000.00,"growth":"+6.2%"},
            {"name":"Dividend Stocks","type":"Income","amount":250.00,"growth":"+2.0%"}
        ]
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()

        # ✅ CHECK IF USER EXISTS
        if user:

            # ✅ BLOCK CHECK
            if user.is_blocked:
                return redirect(url_for('blocked'))

            # ✅ PASSWORD CHECK
            if check_password_hash(user.password, request.form.get('password')):

                # 🔥 SET ADMIN PROPERLY
                if user.email == "j99310482@gmail.com":
                    user.is_admin = True
                else:
                    user.is_admin = False

                db.session.commit()

                login_user(user)

                print("IS ADMIN:", user.is_admin)  # DEBUG

                # 🔥 CORRECT REDIRECT
                if user.is_admin:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('dashboard'))

        # ❌ LOGIN FAILED
        flash('Login failed. Check your details.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        email = request.form.get('email')
        name = request.form.get('full_name')
        password = request.form.get('password')

        # ✅ ADD THIS CHECK
        if not email or not name or not password:
            flash("All fields are required.")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('User already exists.')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)

        new_user = User(email=email, full_name=name, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        generate_fake_transactions(new_user)

        return redirect(url_for('login'))

    return render_template('register.html')
    

@app.route('/dashboard')
@login_required
def dashboard():

     if not current_user.transfer_pin:
        return redirect(url_for('set_pin'))
        
     transactions = Transaction.query.filter_by(
        sender_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    # TOTAL TRANSFER
     total_transfer = sum(t.amount for t in transactions if t.transaction_type == 'debit')

    # LAST DATE
     last_date = transactions[0].date if transactions else datetime.utcnow()

    # LAST DAY TRANSACTIONS
     today_tx = [t for t in transactions if t.date.date() == last_date.date()]

    # PREVIOUS MONTH
     prev_month_tx = [t for t in transactions if t.date.month == last_date.month - 1]

    # TWO RANDOM NAMES
     names = [t.receiver_name for t in transactions[:5]]
     send1 = names[0] if len(names) > 0 else "Jacob"
     send2 = names[1] if len(names) > 1 else "Mom"

     return render_template('dashboard.html',
        user=current_user,
        transactions=transactions,
        total_transfer=total_transfer,
        today_tx=today_tx,
        prev_month_tx=prev_month_tx,
        send1=send1,
        send2=send2
     )
@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():

    file = request.files.get('profile_pic')

    if file and file.filename != '':
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")

        filepath = os.path.join('static/uploads', filename)
        file.save(filepath)

        current_user.profile_pic_path = filename
        db.session.commit()

    return redirect('/settings')

@app.route('/go_to_pin', methods=['POST'])
@login_required
def go_to_pin():
    
    bank = request.form.get('bank')
    account_number = request.form.get('account_number')
    receiver_name = request.form.get('receiver_name')
    address = request.form.get('address')
    amount = request.form.get('amount')

    session['transfer_data'] = {
        'bank': bank,
        'account_number': account_number,
        'receiver_name': receiver_name,
        'address': address,
        'amount': amount
    }

    return redirect(url_for('confirm_pin'))  # ✅ MUST BE INSIDE FUNCTION

@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_transfer():

    if request.method == 'POST':

        if request.form.get('otp') == session.get('otp'):

            transfer_data = session.get('transfer_data')

            if not transfer_data:
                flash("Session expired.")
                return redirect(url_for('transfer'))

            amount = float(transfer_data['amount'])

            if current_user.balance < amount:
                flash("Insufficient balance.")
                return redirect(url_for('transfer'))

            # ✅ Deduct balance
            current_user.balance -= amount

            # ✅ Save transaction
            db.session.add(Transaction(
                sender_id=current_user.id,
                receiver_name=transfer_data['receiver_name'],
                account_number=transfer_data.get('account_number', '00000000'),
                amount=amount,
                transaction_type='debit',
                date=datetime.utcnow()
            ))

            db.session.commit()

            # OPTIONAL bonus
            if random.choice([True, False]):
                add_random_credit(current_user)

            # ✅ Data for success page
            receiver_name = transfer_data['receiver_name']
            bank = transfer_data['bank']
            reference = "TRX" + str(random.randint(100000, 999999))  
            date = datetime.utcnow() 

            # ✅ Clear session
            session.pop('otp', None)
            session.pop('transfer_data', None)

            return render_template(
                "transfer_success.html",
                receiver=receiver_name,
                sender=current_user.full_name,
                amount=amount,
                bank=bank,
                reference=reference,
                date=date
            )

        flash("Invalid code.")
        return redirect(url_for('verify_transfer'))

    return render_template('verify.html')

@app.route('/transactions')
@login_required
def transactions():
    transactions_db = Transaction.query.filter_by(
        sender_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    grouped_transactions = defaultdict(list)

    for t in transactions_db:
        month_key = t.date.strftime("%B %Y")  # e.g. "March 2026"

        grouped_transactions[month_key].append({
            "date": t.date.strftime("%b %d, %Y"),
            "name": t.receiver_name if t.receiver_name else "Unknown",
            "amount": t.amount,
            "type": "debit" if t.transaction_type == "debit" else "credit"
        })

    return render_template("transactions.html", grouped=grouped_transactions)
    

@app.route('/transfer_success')
@login_required
def transfer_success():
    return render_template('transfer_success.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        file = request.files.get('profile_pic')

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            current_user.profile_pic_path = filename
            db.session.commit()

            flash('Profile picture updated!', 'success')

        return redirect(url_for('settings'))

    return render_template('settings.html', user=current_user)

@app.route("/balance")
def get_balance():
    return {"balance": current_user.balance}  

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():

    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']

        # check old password
        if not check_password_hash(current_user.password, old):
            return "Old password incorrect"

        # update password
        current_user.password = generate_password_hash(new)
        db.session.commit()

        return redirect('/settings')

    return render_template('change_password.html')

@app.route('/confirm_pin', methods=['GET', 'POST'])
@login_required
def confirm_pin():

    if request.method == 'POST':

        entered_pin = request.form.get('pin')

        if entered_pin != current_user.transfer_pin:
            flash("Incorrect PIN")
            return redirect(url_for('confirm_pin'))

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp

        print("OTP:", otp)

        # ✅ SAFE EMAIL (WILL NOT CRASH)
        try:
            msg = Message(
                "UnityBank OTP Code",
                recipients=[current_user.email]
            )
            msg.body = f"Your OTP code is: {otp}"
            mail.send(msg)
        except Exception as e:
            print("MAIL ERROR:", e)

        # ALWAYS CONTINUE
        return redirect(url_for('verify_transfer'))

    return render_template('enter_pin.html')
    
@app.route('/review_transfer', methods=['POST'])
@login_required
def review_transfer():
    session['bank'] = request.form['bank']
    session['account'] = request.form['account']
    session['name'] = request.form['name']
    session['address'] = request.form.get('address')
    session['amount'] = request.form['amount']

    return render_template('review_transfer.html')


@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    return render_template('transfer.html', user=current_user)
    

    if user.pin != entered_pin:
        flash("Incorrect PIN")
        return redirect('/transfer')

    if not user.pin:
         return redirect(url_for('set_pin'))

@app.route('/set-pin', methods=['GET', 'POST'])
@login_required
def set_pin():
    if request.method == 'POST':
        pin = request.form.get('pin')

        current_user.transfer_pin = pin
        db.session.commit()

        flash('PIN set successfully')
        return redirect(url_for('dashboard'))

    return render_template('setpin.html')

@app.route('/make_admin')
def make_admin():
    user = User.query.all()

    for u in user:
        print(u.email, u.is_admin)  # 👈 DEBUG

    user = User.query.filter_by(email="j99310482@gmail.com").first()

    if user:
        user.is_admin = True
        db.session.commit()
        return "You are now admin"

    return "User not found"

@app.route('/admin')
@login_required
def admin():

    if not current_user.is_admin:
        return "Access Denied"

    users = User.query.all()
    total_users = User.query.count()

    return render_template(
        'admin.html',
        users=users,
        total_users=total_users
    )
    
@app.route('/toggle_block/<int:user_id>')
@login_required
def toggle_block(user_id):

    if not current_user.is_admin:
        return "Unauthorized"

    user = User.query.get(user_id)

    user.is_blocked = not user.is_blocked
    db.session.commit()

    return redirect(url_for('admin'))

@app.before_request
def block_check():
    if current_user.is_authenticated and current_user.is_blocked:
        logout_user()
        return redirect(url_for('blocked'))

@app.route('/blocked')
def blocked():
    return render_template('blocked.html')


@app.route('/support')
def support():
    return render_template('support.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))