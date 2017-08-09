from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, SignupForm
from .models import User

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user 
    posts = [  # fake array of posts
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
                           title='Home',
                           user=user,
                           posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None:
            login_user(user)
    	    flash('Login successful!')
    	    return redirect(url_for('index'))
        flash('Incorrect username or password.')
    return render_template('login.html', 
                           title='Sign In',
                           form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        new_user = User(username = form.username.data,
                               firstname= form.firstname.data,
                               lastname = form.lastname.data,
                               email = form.email.data,
                               nickname = form.nickname.data,
                               password = form.password.data)
        
        flash('Welcome to Loudspeaker %s!' % (form.firstname.data))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', title='Create an Account', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))