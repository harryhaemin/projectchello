from app.models.models import Song


# custom exception for song
class SongException(Exception):
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


class SongController():
	session = None

	def __init__(self, session):
		self.session = session

	def get_songs(self, playlist_id):
		# get list of songs for a playlist
		songs = Song.query.filter_by(playlist_id=playlist_id).all()
		return songs

	def add_song(self, playlist_id, title, url, source_id, thumbnail, source, duration):
		# check if song is already in the playlist
		song = Song.query.filter_by(url=url, playlist_id=playlist_id).first()
		if song:
			raise SongException('Song is already added')

		# add new song to the playlist
		song = Song(playlist_id, title, url, source_id, thumbnail, source, duration)
		self.session.add(song)
		self.session.commit()

		# return the added song
		return song

	def delete_song(self, playlist_id, song_id):
		# delete the song with given ID from the playlist
		song = Song.query.filter_by(id=song_id, playlist_id=playlist_id).first()
		if not song:
			raise SongException('Song id <%s> does not exist' % song_id)

		self.session.delete(song)
		self.session.commit()

		return None
