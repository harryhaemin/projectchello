from app import db, bcrypt, login_manager
import json


def to_json(inst, cls):
	# Return a dict for the sql query result
	convert = dict()
	d = dict()
	for column in cls.__table__.columns:
		value = getattr(inst, column.name)
		if column.type in convert.keys() and value is not None:
			try:
				d[column.name] = convert[column.type](value)
			except:
				d[column.name] = "Error:  Failed to covert using ", str(convert[column.type])
		elif value is None:
			d[column.name] = str()
		else:
			d[column.name] = value
	return d


class Playlist(db.Model):
	# create a model for playlist
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), nullable=False)
	owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __init__(self, name, owner_id):
		self.name = name
		self.owner_id = owner_id

	@property
	def serialize(self):
		return to_json(self, self.__class__)


class UserCollaborates(db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)

	def __init__(self, user_id, playlist_id):
		self.user_id = user_id
		self.playlist_id = playlist_id

	@property
	def serialize(self):
		return to_json(self, self.__class__)


class Song(db.Model):
	# create a model for song
	id = db.Column(db.Integer, primary_key=True)
	playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
	title = db.Column(db.String(80), nullable=False)
	url = db.Column(db.String(200), nullable=False)
	source_id = db.Column(db.String(50), nullable=False)
	thumbnail = db.Column(db.String(200))
	source = db.Column(db.String(50))
	duration = db.Column(db.Integer)

	def __init__(self, playlist_id, title, url, source_id, thumbnail=None, source=None, duration=None):
		self.playlist_id = playlist_id
		self.title = title
		self.url = url
		self.source_id = source_id
		self.thumbnail = thumbnail
		self.source = source
		self.duration = duration

	@property
	def serialize(self):
		return to_json(self, self.__class__)


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True)
	password = db.Column(db.String(20), nullable=False)
	first_name = db.Column(db.String(20), nullable=False)
	last_name = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return '<Username %r>' % (self.username)

	def __init__(self, username, password, first_name, last_name):
		self.username = username
		self.password = bcrypt.generate_password_hash(password)
		self.first_name = first_name
		self.last_name = last_name

	@login_manager.user_loader
	def load_user(id):
		return User.query.get(int(id))

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.id

	def verify_password(self, password):
		return bcrypt.check_password_hash(self.password, password)

	@property
	def serialize(self):
		return to_json(self, self.__class__)
