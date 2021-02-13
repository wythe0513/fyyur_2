#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import operator
import dateutil.parser
import babel
from sqlalchemy import func
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort, session
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# by SF
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#



class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String()))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    adress = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_talent_description = db.Column(db.String())
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean)
    seeking_talent_description = db.Column(db.String())
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale = 'en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
    venues_list = Venue.query.order_by(Venue.city, Venue.state).all()
    data = []
    city_state = ''
    for venue in venues_list:
        num_upcoming_shows = db.session.query(Venue).join(Show).\
            filter(Venue.id == venue.id, Show.start_time > datetime.now()).count()
        if city_state == venue.city + venue.state:
            data[len(data) - 1]['venues'].append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': num_upcoming_shows
            })
        else:
            data.append({
                'city': venue.city,
                'state': venue.state,
                'venues': [{
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': num_upcoming_shows
                }]
            })
            city_state = venue.city + venue.state

    return render_template('pages/venues.html', areas=data)

# -----------------------------------------------------------
#  data=[{
#    "city": "San Francisco",
#    "state": "CA",
#    "venues": [{
#      "id": 1,
#      "name": "The Musical Hop",
#      "num_upcoming_shows": 0,
#    }, {
#      "id": 3,
#      "name": "Park Square Live Music & Coffee",
#      "num_upcoming_shows": 1,
#    }]
 # }, {
#    "city": "New York",
#    "state": "NY",
#    "venues": [{
#      "id": 2,
#      "name": "The Dueling Pianos Bar",
#      "num_upcoming_shows": 0,
#    }]
#  }]
# ---------------------------------------------------------------

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    search_results = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    data = []
    for result in search_results:
        data.append({
            "id": result.id,
            "name": result.name,
            "num_of_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
        })
    response = {}
    response['count'] = len(search_results)
    response['data'] = data


  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  #response={
  #  "count": 1,
  #  "data": [{
  #    "id": 2,
  #    "name": "The Dueling Pianos Bar",
  #    "num_upcoming_shows": 0,
  #  }]
  #}
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    if not venue:
        return(render_template('errors/404.html'))

    all_shows = Show.query.filter_by(venue_id=venue_id).all()
    past_shows = []
    upcoming_shows = []
    for show in all_shows:
        result = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(result)
        else:
            past_shows.append(result)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "adress": venue.adress,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # data1={
  #  "id": 1,
  #  "name": "The Musical Hop",
  #  "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #  "address": "1015 Folsom Street",
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "123-123-1234",
  #  "website": "https://www.themusicalhop.com",
  #  "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #  "seeking_talent": True,
  #  "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #  "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #  "past_shows": [{
  #    "artist_id": 4,
  #    "artist_name": "Guns N Petals",
  #    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #    "start_time": "2019-05-21T21:30:00.000Z"
  #  }],
  #  "upcoming_shows": [],
  #  "past_shows_count": 1,
  #  "upcoming_shows_count": 0,
  #}
  #data2={
  #  "id": 2,
  #  "name": "The Dueling Pianos Bar",
  #  "genres": ["Classical", "R&B", "Hip-Hop"],
  #  "address": "335 Delancey Street",
  #  "city": "New York",
  #  "state": "NY",
  #  "phone": "914-003-1132",
  #  "website": "https://www.theduelingpianos.com",
  #  "facebook_link": "https://www.facebook.com/theduelingpianos",
  #  "seeking_talent": False,
  #  "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
  #  "past_shows": [],
  #  "upcoming_shows": [],
  #  "past_shows_count": 0,
  #  "upcoming_shows_count": 0,
  #}
  #data3={
  #  "id": 3,
  #  "name": "Park Square Live Music & Coffee",
  #  "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
  #  "address": "34 Whiskey Moore Ave",
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "415-000-1234",
  #  "website": "https://www.parksquarelivemusicandcoffee.com",
  #  "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
  #  "seeking_talent": False,
  #  "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #  "past_shows": [{
  #    "artist_id": 5,
  #    "artist_name": "Matt Quevedo",
  #    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #    "start_time": "2019-06-15T23:00:00.000Z"
  #  }],
  #  "upcoming_shows": [{
  #    "artist_id": 6,
  #    "artist_name": "The Wild Sax Band",
  #    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #    "start_time": "2035-04-01T20:00:00.000Z"
  #  }, {
  #    "artist_id": 6,
  #    "artist_name": "The Wild Sax Band",
  #    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #    "start_time": "2035-04-08T20:00:00.000Z"
  #  }, {
  #    "artist_id": 6,
  #    "artist_name": "The Wild Sax Band",
  #    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #    "start_time": "2035-04-15T20:00:00.000Z"
  #  }],
  #  "past_shows_count": 1,
  #  "upcoming_shows_count": 1,
  #}
  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
      form = VenueForm()
      name = form.name.data
      city = form.city.data
      state = form.state.data
      adress = form.adress.data
      phone = form.phone.data
      genres = form.genres.data
      image_link = form.image_link.data
      facebook_link = form.facebook_link.data
      website = form.website.data
      seeking_talent = True if 'seeking_talent' in request.form else False
      seeking_talent_description = form.seeking_talent_description.data

      venue = Venue(name=name, city=city, state=state, adress=adress, phone=phone, genres=genres, image_link=image_link,
                      facebook_link=facebook_link, website=website, seeking_talent=seeking_talent,
                      seeking_talent_description=seeking_talent_description)

      db.session.add(venue)
      db.session.commit()

  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())

  finally:
      db.session.close()

  if not error:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  else:
      flash('An error occured.  Venue ' + request.form['name'] + ' could not be listed.' )

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/exept ValueError as e:

  return render_template('pages/home.html')

  @app.route('/venues/<venue_id>', methods=['POST'])
  def delete_venue(venue_id):

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
      try:
        venue = Venue.query.filter_by(id=venue_id).first_or_404()
        # current_session = db.object_session(venue)
        # current_session.delete(venue)
        # current_session.commit()
        db.session.delete(venue)
        db.session.commit()
        flash('The venue has been removed together with all of its shows.')
        return render_template('pages/home.html')

      except ValueError:
        flash('It was not possible to delete this Venue')

      return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = []
  if not artists:
      return render_template('/errors/404.html')

  for artist in artists:
      data.append({
          "id":artist.id,
          "name": artist.name
      })

  # data=[{
  #  "id": 4,
  #  "name": "Guns N Petals",
  #}, {
  #  "id": 5,
  #  "name": "Matt Quevedo",
  #}, {
  #  "id": 6,
  #  "name": "The Wild Sax Band",
  # }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  data = []
  search_query = request.form.get('search_term', '')
  search_artist = Artist.query.filter(
      Artist.name.ilike(f'%{search_query}%')).all()
  for result in search_artist:
      data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(Show.query.filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all())
        })
  response = {}
  response['count'] = len(search_artist)
  response['data'] = data


  # response={
  #  "count": 1,
  #  "data": [{
  #    "id": 4,
  #    "name": "Guns N Petals",
  #    "num_upcoming_shows": 0,
  #  }]
  #}

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_query = Artist.query.get(artist_id)

    if not artist_query:
        return render_template('errors/404.html')

    all_shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    for show in all_shows:
        result = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(result)
        else:
            past_shows.append(result)

    data = {
        "id": artist_query.id,
        "name": artist_query.name,
        "genres": artist_query.genres,
        "city": artist_query.city,
        "state": artist_query.state,
        "phone": artist_query.phone,
        "website": artist_query.website,
        "facebook_link": artist_query.facebook_link,
        "seeking_talent": artist_query.seeking_talent,
        "seeking_talent_description": artist_query.seeking_talent_description,
        "image_link": artist_query.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id


  #data1={
  #  "id": 4,
  #  "name": "Guns N Petals",
  #  "genres": ["Rock n Roll"],
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "326-123-5000",
  #  "website": "https://www.gunsnpetalsband.com",
  #  "facebook_link": "https://www.facebook.com/GunsNPetals",
  #  "seeking_venue": True,
  #  "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #  "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #  "past_shows": [{
  #    "venue_id": 1,
  #    "venue_name": "The Musical Hop",
  #    "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #    "start_time": "2019-05-21T21:30:00.000Z"
  #  }],
  #  "upcoming_shows": [],
  #  "past_shows_count": 1,
  #  "upcoming_shows_count": 0,
  #}
  #data2={
  #  "id": 5,
  #  "name": "Matt Quevedo",
  #  "genres": ["Jazz"],
  #  "city": "New York",
  #  "state": "NY",
  #  "phone": "300-400-5000",
  #  "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #  "seeking_venue": False,
  #  "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #  "past_shows": [{
  #    "venue_id": 3,
  #    "venue_name": "Park Square Live Music & Coffee",
  #    "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #    "start_time": "2019-06-15T23:00:00.000Z"
  #  }],
  #  "upcoming_shows": [],
  #  "past_shows_count": 1,
  #  "upcoming_shows_count": 0,
  #}
  #data3={
  #  "id": 6,
  #  "name": "The Wild Sax Band",
  #  "genres": ["Jazz", "Classical"],
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "432-325-5432",
  #  "seeking_venue": False,
  #  "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #  "past_shows": [],
  #  "upcoming_shows": [{
  #    "venue_id": 3,
  #    "venue_name": "Park Square Live Music & Coffee",
  #    "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #    "start_time": "2035-04-01T20:00:00.000Z"
  #  }, {
  #    "venue_id": 3,
  #    "venue_name": "Park Square Live Music & Coffee",
  #    "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #    "start_time": "2035-04-08T20:00:00.000Z"
  #  }, {
  #    "venue_id": 3,
  #    "venue_name": "Park Square Live Music & Coffee",
  #    "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #    "start_time": "2035-04-15T20:00:00.000Z"
  #  }],
  #  "past_shows_count": 0,
  #  "upcoming_shows_count": 3,
  #}
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Venue.query.first_or_404(artist_id)
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

 # form = ArtistForm()
 # artist = Artist.query.get(artist_id)

  #if artist:
    #   form.name.data = artist.name
    #   form.city.data = artist.city
    #   form.state.data = artist.state
    #   form.phone.data = artist.phone
    #   form.genres.data = artist.genres
    #   form.facebook_link.data = artist.facebook_link
    #   form.image_link.data = artist.image_link
    #   form.website.data = artist.website

  #form.seeking_venue.data = artist.seeking_venue
  #form.seeking_talent_description.data = artist.seeking_talent_description


  #artist={
  #  "id": 4,
  #  "name": "Guns N Petals",
  #  "genres": ["Rock n Roll"],
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "326-123-5000",
  #  "website": "https://www.gunsnpetalsband.com",
  #  "facebook_link": "https://www.facebook.com/GunsNPetals",
  #  "seeking_venue": True,
  #  "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #  "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  #}
  # TODO: populate form with fields from artist with ID <artist_id>
  #return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    try:
        artist = Artist.query.first_or_404(artist_id)
        form.populate_obj(artist)
        db.session.commit()
        flash(f'Artist {form.name.data} was successfully edited!')
    except ValueError as e:
        db.session.rollback()
        flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


    #error = False
    #artist = Artist.query.get(artist_id)
    #form = request.form.to_dict(True)
    #genres = request.form.getlist('genres')
    # seeking_venue = bool(request.form.get('seeking_venue'))
    #try:
    #    artist.name = form.name.data
    #    artist.name = form.name.data
    #    artist.phone = form.phone.data
    #    artist.state = form.state.data
    #    artist.city = form.city.data
    #    artist.genres = form.getlist('genres')
    #    artist.image_link = form.image_link.data
    #    artist.facebook_link = form.facebook_link.data
    #    db.session.add(artist)
    #    db.session.commit()
    #except:
    #    error = True
    #    db.session.rollback()
    #    print(sys.exc_info())
    #finally:
    #    db.session.close()
    #if error:
    #    flash('An error occurred. Artist could not be changed.')
    #if not error:
    #    flash('Artist was successfully updated!')

  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

    #return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.first_or_404(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

 # form = VenueForm()
 # venue = Venue.query.get(venue_id)

  #form.name.data = venue.name
  #form.city.data = venue.city
  #form.state.data = venue.state
  #form.phone.data = venue.phone
  #form.adress.data = venue.adress
  #form.genres.data = venue.genres
  #form.facebook_link.data = venue.facebook_link
  #form.image_link.data = venue.image_link
  #form.website.data = venue.website
  #form.seeking_talent.data = venue.seeking_talent
  #form.seeking_talent_description.data = venue.seeking_talent_description

  #venue={
  #  "id": 1,
  #  "name": "The Musical Hop",
  #  "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #  "address": "1015 Folsom Street",
  #  "city": "San Francisco",
  #  "state": "CA",
  #  "phone": "123-123-1234",
  #  "website": "https://www.themusicalhop.com",
  #  "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #  "seeking_talent": True,
  #  "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #  "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  #}
  # TODO: populate form with values from venue with ID <venue_id>
  #return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    try:
        venue = Venue.query.first_or_404(venue_id)
        form.populate_obj(venue)
        db.session.commit()
        flash(f'Venue {form.name.data} was successfully edited!')
    except ValueError as e:
        db.session.rollback()
        flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

    #error = False
    #form = request.form.to_dict(True)
    #genres = request.form.getlist('genres')
    #try:
    #    form = VenueForm()
    #    venue = Venue.query.get(venue_id)
    #    name = form.name.data
    #    venue.name = name
    #    venue.genres = form.genres.data
    #    venue.city = form.city.data
    #    venue.state = form.state.data
    #    venue.adress = form.adress.data
    #    venue.phone = form.phone.data
    #    venue.facebook_link = form.facebook_link.data
    #    venue.website = form.website.data
    #    venue.image_link = form.image_link.data
    #    venue.seeking_talent = form.seeking_talent.data
    #    venue.seeking_talent_description = form.seeking_talent_description.data
    #except:
    #    error = True
    #    db.session.rollback()
    #    print(sys.exc_info())
    #finally:
    #    db.session.close()

  # #TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    #return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        form = ArtistForm()
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        image_link = form.image_link.data
        facebook_link = form.facebook_link.data
        artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, image_link=image_link, facebook_link=facebook_link)
        db.session.add(artist)
        db.session.commit()
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success

        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        flash('An error occurred.')
        print(sys.exc_info())
    finally:
        db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show).join(Artist).join(Venue).all()
    data = []

    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  #data=[{
  #  "venue_id": 1,
  #  "venue_name": "The Musical Hop",
  #  "artist_id": 4,
  #  "artist_name": "Guns N Petals",
  #  "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #  "start_time": "2019-05-21T21:30:00.000Z"
  #}, {
  #  "venue_id": 3,
  #  "venue_name": "Park Square Live Music & Coffee",
  #  "artist_id": 5,
  #  "artist_name": "Matt Quevedo",
  #  "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #  "start_time": "2019-06-15T23:00:00.000Z"
  #}, {
  #  "venue_id": 3,
  #  "venue_name": "Park Square Live Music & Coffee",
  #  "artist_id": 6,
  #  "artist_name": "The Wild Sax Band",
  #  "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #  "start_time": "2035-04-01T20:00:00.000Z"
  #}, {
  #  "venue_id": 3,
  #  "venue_name": "Park Square Live Music & Coffee",
  #  "artist_id": 6,
  #  "artist_name": "The Wild Sax Band",
  #  "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #  "start_time": "2035-04-08T20:00:00.000Z"
  #}, {
  #  "venue_id": 3,
  #  "venue_name": "Park Square Live Music & Coffee",
  #  "artist_id": 6,
  #  "artist_name": "The Wild Sax Band",
  #  "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #  "start_time": "2035-04-15T20:00:00.000Z"
  #}]
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        error = True
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()



  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  # flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
