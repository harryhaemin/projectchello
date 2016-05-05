from app.models.models import User
from app import login_manager, bcrypt
from flask.ext.login import login_user, logout_user


# custom exception for authentication
class AuthenticationException(Exception):
	status_code = 400

	def __init__(self, message, status_code=None, payload=None):
		Exception.__init__(self)
		self.message = message
		if status_code is not None:
			self.status_code = status_code
		self.payload = payload

	def to_dict(self):
		rv = dict(self.payload or ())
		rv['message'] = self.message
		return rv


class Authentication():
	session = None

	def __init__(self, session):
		self.session = session

	def authenticate(self, username, password):
		# check if username and password is given
		if username is None or password is None:
			raise AuthenticationException('Username or password is missing')

		username = username.lower()

		user = User.query.filter_by(username=username).first()
		if user:
			# check if password is valid
			if bcrypt.check_password_hash(user.password, password):
				login_user(user, remember=True)
				return user

			# raise exception if invalid credentials are given
			raise AuthenticationException('Invalid username or password')

		raise AuthenticationException('Username \"%s\" not found' % username) # user not found

	def register(self, username, password, first_name, last_name):
		# check if username and password is given
		if username is None or password is None:
			raise AuthenticationException('Username or password is missing')

		username = username.lower()

		if User.query.filter_by(username = username).first() is not None:
			raise AuthenticationException('Username \"%s\" already exists' % username)

		# add new user to the database
		user = User(username, password, first_name, last_name)
		self.session.add(user)
		self.session.commit()

		login_user(user, remember=True)
		return user

	def logout(self):
		logout_user()
		return True

class UserController():
	session = None

	def __init__(self, session):
		self.session = session

	def get_users(self):
		users = User.query.all()
		return users

	def get_user(self, user_id):
		user = User.query.filter_by(id=user_id).first()
		return user


@login_manager.user_loader
def user_loader(user_id):
  return User.query.get(user_id)











