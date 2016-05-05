from app.models.models import Playlist
from app.models.models import User
from app.models.models import UserCollaborates
from app.controllers.song_controller import SongController


# custom exception for playlist
class PlaylistException(Exception):
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


class PlaylistController():
	session = None

	def __init__(self, session):
		self.session = session

	def get_playlists(self):
		# get list of playlists for a user
		playlists = Playlist.query.all()
		return playlists

	def get_playlists_for_user(self, user_id):
		# get list of playlists for a user
		collaborator = UserCollaborates.query.filter_by(user_id=user_id).all()
		playlists_id = [c.playlist_id for c in collaborator]

		playlists = Playlist.query.filter(User.id.in_(playlists_id)).all()
		return playlists

	def get_playlist(self, playlist_id):
		# get playlist for a given playlist_id
		playlist = Playlist.query.filter_by(id=playlist_id).first()
		collaborators = UserCollaborates.query.filter_by(playlist_id=playlist_id).all()
		return playlist, collaborators

	def get_playlist_with_owner(self, user_id, playlist_id):
		# get playlist for a given playlist_id and user
		playlist = Playlist.query.filter_by(user_id=user_id, id=playlist_id).first()
		return playlist

	def create_playlist(self, user_id, name):
		# check if playlist with given name is already in the database
		playlist = Playlist.query.filter_by(owner_id=user_id, name=name).first()
		if playlist:
			raise PlaylistException('Playlist name \"%s\" already exists' % name)

		# add new playlist to the database
		playlist = Playlist(name, user_id)
		self.session.add(playlist)
		self.session.commit()

		collaborator = UserCollaborates(user_id, playlist.id)
		self.session.add(collaborator)
		self.session.commit()

		# return the created playlist
		return playlist

	def update_playlist(self, user_id, playlist_id, name):
		# check if playlist with new name is already in the database
		playlist = Playlist.query.filter_by(user_id=user_id, name=name).first()
		if playlist:
			raise PlaylistException('Playlist name \'%s\' already exists' % name)

		# check if playlist with given playlist_id is not in the database
		playlist = self.get_playlist(user_id, playlist_id)
		if not playlist:
			raise PlaylistException('Playlist id <%s> not found' % playlist_id)

		# update playlist to the database
		playlist.name = name
		self.session.commit()

		# return the updated playlist
		return playlist

	def delete_playlist(self, user_id, playlist_id):
		song_controller = SongController(self.session)

		playlist = self.get_playlist_with_owner(user_id, playlist_id)

		# check if playlist with given playlist_id is not in the database
		if not playlist:
			raise PlaylistException('Playlist id <%s> not found' % playlist_id)

		# delete all songs that belong to that playlist first
		songs = song_controller.get_songs(playlist_id)
		[self.session.delete(song) for song in songs]

		# delete the empty playlist
		self.session.delete(playlist)
		self.session.commit()

		return None

	def verify_playlist_owner(self, user_id, playlist_id):
		playlist = Playlist.query.filter_by(id=playlist_id).first()
		# if playlist is not found, return False
		if not playlist:
			return False

		# if playlist user ID matches the current user's id, return True
		if playlist.owner_id == user_id:
			return True

		# else, return False
		return False

	def verify_playlist_collaborator(self, user_id, playlist_id):
		playlists = UserCollaborates.query.filter_by(playlist_id=playlist_id).all()
		# if playlist is not found, return False
		if len(playlists) == 0:
			return False

		# if playlist user ID matches the current user's id, return True
		for p in playlists:
			if p.user_id == user_id:
				return True
		# else, return False
		return False
