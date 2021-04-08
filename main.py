# flask framework
from flask import Flask, render_template, request, make_response, session, redirect, abort
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

# models
from data import db_session
from data.users import User

# forms
from forms.register_form import RegisterForm
from forms.login_form import LoginForm


# extra modules
import datetime

# flask init
app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# login manager init
login_manager = LoginManager()
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# home page
@app.route("/")
def index():
    db_sess = db_session.create_session()
    return render_template("base.html")


# register page
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    # register button
    if form.validate_on_submit():
        # check password match
        if form.password.data != form.password_again.data:
            # passwords isn't match
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        # new session
        db_sess = db_session.create_session()
        # check registered
        if db_sess.query(User).filter(User.email == form.email.data).first():
            # this email was registered
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # user data
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # login form
    form = LoginForm()

    # submit button
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # user search
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        # check password
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # go home
            return redirect("/")

        # user error
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    # return template
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")



def main():
    # initilize database
    db_session.global_init("db/blogs.db")

    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
