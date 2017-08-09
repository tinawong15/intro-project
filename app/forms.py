from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email
from .models import User

class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class SignupForm(Form):
	firstname = StringField('firstname', validators=[DataRequired()])
	lastname = StringField('lastname', validators=[DataRequired()])
	nickname = StringField('nickname', validators=[DataRequired()])
	username = StringField('username', validators=[DataRequired()])
	password = PasswordField('password', validators=[DataRequired(), EqualTo('password2', message='Passwords must match.')])
	password2 = PasswordField('password2', validators=[DataRequired()])
	email = StringField('email', validators=[DataRequired(), Email()])
	submit = SubmitField()

	def validate_on_submit(self):
		if not Form.validate_on_submit(self):
			return False

		isError = False
		if User.query.filter_by(email=self.email.data).first():
			self.email.errors.append("This email is already in use.")
			isError = True

		if User.query.filter_by(username = self.username.data).first():
			self.username.errors.append("This username is already in use.")
			isError = True

		return not isError