from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Snippet
from forms import RegisterForm, LoginForm, SnippetForm


app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///snippets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    search = request.args.get("search")
    if search:
        snippets = Snippet.query.filter(
            Snippet.user_id == current_user.id,
            Snippet.title.contains(search)
        ).all()
    else:
        snippets = current_user.snippets
    return render_template("dashboard.html", snippets=snippets)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_snippet():
    form = SnippetForm()
    if form.validate_on_submit():
        snippet = Snippet(
            title=form.title.data,
            category=form.category.data,
            code=form.code.data,
            owner=current_user
        )
        db.session.add(snippet)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_snippet.html", form=form)

@app.route("/delete/<int:id>")
@login_required
def delete_snippet(id):
    snippet = Snippet.query.get(id)
    if snippet.owner == current_user:
        db.session.delete(snippet)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
