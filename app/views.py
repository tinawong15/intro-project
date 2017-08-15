from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, SignupForm, EditForm, PostForm, ForgotUsernameForm, ForgotPasswordForm
from .models import User, Post
from datetime import datetime
from emails import follower_notification, followee_notification, forgot_username_email, forgot_password_email
import hashlib
from random import randint
from config import ADMINS

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
    
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/stats', methods=['GET'])
@login_required
def stats():
    post_count = Post.query.count()
    user_count = User.query.count()
    return render_template('stats.html', post_count=post_count, user_count=user_count)

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = g.user.followed_posts().order_by(Post.timestamp.desc()).all()
    return render_template('index.html',
                           title='Home',
                           form=form,
                           posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        hashedPassword = hashlib.sha256(form.password.data).hexdigest()
        user = User.query.filter_by(username=form.username.data,
                                    password=hashedPassword).all()
        if len(user) > 0:
            login_user(user[0])
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
                        password = hashlib.sha256(form.password.data).hexdigest())
        if form.email.data in ADMINS:
            new_user.is_admin = True
        else:
            new_user.is_admin = False
        flash('Welcome to Loudspeaker %s!' % (form.firstname.data))
        db.session.add(new_user)
        db.session.commit()
        db.session.add(new_user.follow(new_user))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', title='Create an Account', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/users')
def users():
    users = User.query.all()
    users.remove(g.user)
    return render_template('users.html', users=users, u=g.user, title='Users')

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',
                           user=user,
                           posts=posts,
                           title=username)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        if form.nickname.data:
            g.user.nickname = form.nickname.data
        if form.about_me.data:
            g.user.about_me = form.about_me.data
        if form.password.data:
            g.user.password = hashlib.sha256(form.password.data).hexdigest()
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form, title='Edit Profile')
   
@app.route('/edit/<id>', methods=['POST', 'GET'])
@login_required
def editPost(id):
    post = Post.query.filter_by(id=id).first()
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.post.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('index'))
    else:
        form.post.data = post.body
    return render_template('editpost.html', form=form, title='Edit post')

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', username=username))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + username + '.')
        return redirect(url_for('user', username=username))
    db.session.add(u)
    db.session.commit()
    follower_notification(user, g.user)
    followee_notification(user, g.user)
    flash('You are now following ' + username + '!')
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', username=username))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + username + '.')
        return redirect(url_for('user', username=username))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + username + '.')
    return redirect(url_for('user', username=username))

@app.route('/posts')
def posts():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('posts.html',
                           posts=posts,
                           title='All posts')

@app.route('/delete_post/<int:id>', methods=['GET'])
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash('Post not found')
        return redirect(url_for('index'))

    if post.author == g.user or g.user.is_admin:
        db.session.delete(post)
        db.session.commit()
        flash('Post has been deleted.')
        return redirect(url_for('index'))

@app.route('/delete_user/<int:id>', methods=["GET"])
@login_required
def delete_user(id):
    if id == g.user.id or g.user.is_admin:
        user = User.query.filter_by(id=id)
        Post.query.filter_by(author=user.first()).delete()
        user.delete()
        db.session.commit()
    return redirect(url_for('index'))        

@app.route('/forgot_username', methods=['GET', 'POST'])
def forgot_username():
    form = ForgotUsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('There are no users with that email')
            return redirect(url_for('forgot_username'))
        forgot_username_email(user)
        flash('An email has been sent to %s' % form.email.data)
        return redirect(url_for('index'))
    return render_template('forgot_username.html',
                           title='Forgot username',
                           form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        user2 = User.query.filter_by(username=form.username.data).first()
        if user is None or user != user2:
            flash('There are no users with that username and email')
            return redirect(url_for('forgot_password'))
        temp_password = gen_password()
        user.password = hashlib.sha256(temp_password).hexdigest()
        db.session.commit()
        forgot_password_email(user, temp_password)
        flash('An email has been sent to %s' % form.email.data)
        return redirect(url_for('index'))
    return render_template('forgot_password.html',
                           title='Forgot password',
                           form=form)

def gen_password():
    chars = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
    password = ''
    for i in range(8):
        password += chars[randint(0, len(chars)-1)]
    return password
