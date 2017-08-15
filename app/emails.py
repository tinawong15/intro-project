from flask import render_template
from flask_mail import Message
from app import mail
from .decorators import async
from config import ADMINS
from app import app


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_email("[Loudspeaker] %s is now following you!" % follower.nickname,
               ADMINS[0],
               [followed.email],
               render_template("follower_email.txt",
                               user=followed, follower=follower),
               render_template("follower_email.html",
                               user=followed, follower=follower))
def followee_notification(followed, follower):
    send_email("[Loudspeaker] You are now following %s!" % followed.nickname,
               ADMINS[0],
               [follower.email],
               render_template("followee_email.txt",
                               user=followed, follower=follower),
               render_template("followee_email.html",
                               user=followed, follower=follower))

def forgot_username_email(user):
    send_email("[Loudspeaker] Forgotten username",
               ADMINS[0],
               [user.email],
               render_template('forgot_username_email.txt',
                               user=user),
               render_template('forgot_username_email.html',
                               user=user))

def forgot_password_email(user, temp_password):
    send_email("[Loudspeaker] Forgotten password",
               ADMINS[0],
               [user.email],
               render_template('forgot_password_email.txt',
                               user=user,
                               temp_password=temp_password),
               render_template('forgot_password_email.html',
                               user=user,
                               temp_password=temp_password))
