from flask import Flask, request, render_template, redirect, url_for, session, json
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim
import mysql.connector
import json


# App initiation and config:------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mapit_key'
db_config = {
    'user': 'root',
    'password': 'Roeroe99RzA!',
    'host': '127.0.0.1',
    'database': 'cities'
}
geolocator = Nominatim(user_agent="mapit_game")
# --------------------------------------------------------------------------------------------------


# Distance Function:--------------------------------------------------------------------------------
def get_distance(lat1, lon1, lat2, lon2):
    r = 6371

    rad_lat1 = radians(lat1)
    rad_lon1 = radians(lon1)
    rad_lat2 = radians(lat2)
    rad_lon2 = radians(lon2)

    dist_lat = rad_lat2 - rad_lat1
    dist_lon = rad_lon2 - rad_lon1

    a = sin(dist_lat / 2) ** 2 + cos(rad_lat1) * cos(rad_lat2) * sin(dist_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = r * c

    return distance
# -----------------------------------------------------------------------------------------------


# Landing page:----------------------------------------------------------------------------------
@app.route('/')
def home_page():
    return render_template('home_page.html')
# -----------------------------------------------------------------------------------------------


# Game start function (session initialization):--------------------------------------------------
@app.route('/start_game')
def start_game():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        game_cities = []
        for level in range(1,6):
            cursor.execute(f"SELECT * FROM cities WHERE level = {level} ORDER BY RAND() LIMIT 5")
            cities = cursor.fetchall()
            game_cities.extend(cities)

        session['game_cities'] = game_cities
        session['current_city_index'] = 0
        session['total_score'] = 0
        session['correct_countries'] = 0
        session['current_level'] = 1

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return redirect(url_for('home_page'))

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for('play_game'))
# -----------------------------------------------------------------------------------------------


# Game interface:--------------------------------------------------------------------------------
@app.route('/play')
def play_game():
    if 'game_cities' not in session or session['current_city_index'] >= len(session['game_cities']):
        return redirect(url_for('game_over'))

    current_index = session['current_city_index']
    city_to_guess = session['game_cities'][current_index]
    countries_count = session['correct_countries']

    return render_template('map.html',
                           city_name=city_to_guess['name'],
                           city_country=city_to_guess['country'],
                           level=session['current_level'],
                           current_index=current_index,
                           city_count_in_level=(current_index % 5) + 1,
                           total_score=session['total_score'],
                           countries_count=countries_count)
# -----------------------------------------------------------------------------------------------


# Guessing function:-----------------------------------------------------------------------------
@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    guess_lat = float(data['lat'])
    guess_lon = float(data['lon'])
    current_index = session['current_city_index']
    correct_city = session['game_cities'][current_index]
    correct_lat = float(correct_city['latitude'])
    correct_lon = float(correct_city['longitude'])
    target_country = correct_city['country']
    penalty = 1

    try:
        location = geolocator.reverse((guess_lat, guess_lon), language='en')

        address = location.raw.get('address', {})

        guessed_country = address.get('country', '')

        is_correct_country = (guessed_country.lower() == target_country.lower())

    except Exception as e:
        print(f"Geocoding error: {e}")
        is_correct_country = False
        guessed_country = "Unknown/Ocean"


    distance = get_distance(guess_lat, guess_lon, correct_lat, correct_lon)

    if not is_correct_country:
        penalty = 2

    if is_correct_country:
        session['correct_countries'] += 1

    session['total_score'] += (distance * penalty)

    session['current_city_index'] += 1

    is_level_end = (session['current_city_index'] % 5 == 0)
    is_game_end = (session['current_city_index'] >= len(session['game_cities']))

    if is_level_end and not is_game_end:
        session['current_level'] += 1

    return json.dumps({
        'status': 'success',
        'correct_lat': correct_lat,
        'correct_lon': correct_lon,
        'distance': distance,
        'total_score': session['total_score'],
        'is_level_end': is_level_end,
        'is_game_end': is_game_end,
        'correct_country': target_country,
        'is_correct_country': is_correct_country,
        'guessed_country': guessed_country,
        'countries_count': session['correct_countries'],
        'current_index': session['current_city_index'],
        'level_message': f"Level {session['current_level'] - 1} complete! Score: {session['total_score']:.0f} km"
    }, default=str)
# -----------------------------------------------------------------------------------------------


# Game over screen and reset session data:-------------------------------------------------------
@app.route('/game_over')
def game_over():
    final_score = round(float(session.get('total_score', 0)), 2)
    correct_countries = session.get('correct_countries', 0)
    session.pop('game_cities', None)
    session.pop('current_city_index', None)
    session.pop('total_score', None)
    session.pop('current_level', None)

    return render_template('game_over.html', final_score=final_score, correct_countries=correct_countries)
#-------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)