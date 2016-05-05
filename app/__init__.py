import os
from flask import Flask, request, abort, render_template, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_required, current_user
from flask.ext.bcrypt import Bcrypt

# set asset directory for templates and static files
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), './static')

app = Flask(__name__, static_url_path='', template_folder=ASSET_DIR, static_folder=ASSET_DIR)
app.config.from_object('config')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

# import model and controller for song, user and playlist
from app.models.models import Song, User, Playlist
from app.controllers.song_controller import SongController, SongException
from app.controllers.user_controller import Authentication, AuthenticationException, UserController
from app.controllers.playlist_controller import PlaylistController, PlaylistException

# initialize the controllers
song_controller = SongController(db.session)
authentication = Authentication(db.session)
user_controller = UserController(db.session)
playlist_controller = PlaylistController(db.session)

# base URL
@app.route('/')
def home():
  return render_template('index.html')

# error handlers for custom exceptions
@app.errorhandler(PlaylistException)
@app.errorhandler(SongException)
@app.errorhandler(AuthenticationException)
def handle_invalid_usage(error):
  response = jsonify(error.to_dict())
  response.status_code = error.status_code
  return response

# API endpoint for getting playlists
#TODO: implement keyword search
@app.route('/api/playlists', methods=['GET'])
@login_required
def get_playlists():
  q = request.args.get('q')
  if q:
    playlists = playlist_controller.get_playlists_by_keyword(q.lower())
  else:
    playlists = playlist_controller.get_playlists()
  return jsonify({'playlists': [playlist.serialize for playlist in playlists]})

# API endpoint for creating playlist for current user
@app.route('/api/playlists', methods=['POST'])
@login_required
def create_playlist():
  name = request.json.get('name')
  user_id = current_user.id
  playlist = playlist_controller.create_playlist(user_id, name)
  return jsonify({'playlist': playlist.serialize})

# API endpoint for deleting an existing playlist for current user
@app.route('/api/playlists/<playlist_id>', methods=['DELETE'])
@login_required
def delete_playlist(playlist_id):
  user_id = current_user.id

  # check if given playlist belongs to current user
  if not playlist_controller.verify_playlist_owner(user_id, playlist_id):
    abort(400)

  # delete playlist
  playlist_controller.delete_playlist(user_id, playlist_id)
  return '', 200

# API endpoint for getting list of songs for a playlist
@app.route('/api/playlists/<playlist_id>', methods=['GET'])
@login_required
def get_playlist(playlist_id):
  user_id = current_user.id

  # check if playlist exists
  playlist, collaborators = playlist_controller.get_playlist(playlist_id)
  if not playlist:
    abort(404)

  songs = song_controller.get_songs(playlist_id)

  # return the playlist as a JSON
  playlist_json = playlist.serialize
  playlist_json['songs'] = [song.serialize for song in songs]
  playlist_json['collaborators'] = [c.user_id for c in collaborators]

  return jsonify({'playlist': playlist_json})

# API endpoint for updating a playlist
@app.route('/api/playlists/<playlist_id>', methods=['PUT'])
@login_required
def update_playlist(playlist_id):
  user_id = current_user.id
  name = request.json.get('name')

  playlist = playlist_controller.update_playlist(user_id, playlist_id, title)

  # get songs that belong to this playlist
  songs = song_controller.get_songs(playlist_id)

  # return the playlist as a JSON
  playlist_json = playlist.serialize
  playlist_json['songs'] = [song.serialize for song in songs]

  return jsonify({'playlist': playlist_json})

# API endpoint for adding a new song
@app.route('/api/playlists/<playlist_id>/songs', methods=['POST'])
@login_required
def add_song(playlist_id):
  song = request.json.get('songs')
  title = song.get('title')
  url = song.get('url')
  source_id = song.get('source_id')
  thumbnail = song.get('thumbnail')
  source = song.get('source')
  duration = song.get('duration')

  user_id = current_user.id

  # check if given playlist belongs to current user
  if not playlist_controller.verify_playlist_collaborator(user_id, playlist_id):
    abort(400)

  song = song_controller.add_song(playlist_id, title, url, source_id, thumbnail, source, duration)
  if song:
    # update count for number of songs in the playlist
    playlist_controller.add_count(user_id, playlist_id)
    return jsonify({'song': song.serialize})

  abort(500)

# API endpoint for adding a new collaborator
# TODO: add collaborator
@app.route('/api/playlists/<playlist_id>/collaborators', methods=['POST'])
@login_required
def add_collaborator(playlist_id):

  return ''

# API endpoint for deleting a song from the playlist
@app.route('/api/playlists/<playlist_id>/songs/<song_id>', methods=['DELETE'])
@login_required
def delete_song(playlist_id, song_id):
  user_id = current_user.id

  # check if given playlist belongs to current user
  if not playlist_controller.verify_playlist_owner(user_id, playlist_id):
    abort(400)

  song_controller.delete_song(playlist_id, song_id)

  # update count for number of songs in the playlist
  playlist_controller.subtract_count(user_id, playlist_id)
  return '', 200

# API endpoint for login
@app.route('/api/login', methods=['POST'])
def login():
  username = request.json.get('username')
  password = request.json.get('password')

  user = authentication.authenticate(username, password)
  if user:
    return jsonify({'user': {'username': user.username}})

  abort(500)

# API endpoint for creating an user account
@app.route('/api/signup', methods=['POST'])
def signup():
  username = request.json.get('username')
  password = request.json.get('password')
  first_name = request.json.get('first_name')
  last_name = request.json.get('last_name')

  user = authentication.register(username, password, first_name, last_name)
  
  if user:
    return jsonify({'user': {'username': user.username}})

  abort(400)

# API endpoint for logout
@app.route('/api/logout', methods=['GET', 'POST'])
@login_required
def logout():
  authentication.logout()
  return '', 200

# API endpoint for getting list of playlists for a user
@app.route('/api/users/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
  user = user_controller.get_user(user_id)
  user_json = user.serialize

  # check if given playlist belongs to current user
  playlists = playlist_controller.get_playlists_for_user(user_id)

  # return the playlist as a JSON
  playlists_json = [playlist.serialize for playlist in playlists]
  user_json['playlists'] = playlists_json

  return jsonify({'user': user_json})

# get list of users route
# TODO: implemenet get_users and get_users_by_keyword
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
  q = request.args.get('q')
  if q:
    users = user_controller.get_users_by_keyword(q.lower())
  else:
    users = user_controller.get_users()
  return jsonify({'users': [user.serialize for user in users]})
