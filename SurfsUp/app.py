from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
from dateutil.relativedelta import relativedelta

# Database Setup
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement_t = Base.classes.measurement
station_t = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes
available_routes = ['precipitation', 'stations', 'tobs']

@app.route("/")
def home():
    html = '''<main style="width: 960px; margin: 0 auto">'''
    html += '''
    <a style="text-decoration: none; color: #008ef6; font-family: system-ui; font-size: 1.5em;" href="/">HOME |</a>
    <h1 style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 2em; font-weight: lighter">Available routes</h1>
    '''
    html+='''<ol style="text-decoration: none;font-family: system-ui; font-size: 1.4em; font-weight: lighter">'''
    for li in available_routes:
        html+=f'''<li> <a style="text-decoration: none; color: #008ef6;" target="_blank" href="/api/v1.0/{li}">{li.title()} <span style="font-size: 0.7em">"/api/v1.0/{li}"</span> &#x279a</a>  </li>'''
    html+="</ol>"
    html+='''<a style="text-decoration: none; color: #008ef6; font-family: system-ui;" href="api/v1.0/2016-08-11">>> Sample start date : "2016-08-11"</a><br>
    <a style="text-decoration: none; color: #008ef6; font-family: system-ui;" href="api/v1.0/2016-08-11/2017-01-01">>> Sample start - end date : "2016-08-11/2017-01-01"</a>'''
    html+="</main>"

    return html

@app.route('/api/v1.0/<path:current_route>')
def current_route(current_route):
  session = Session(engine)
  # Getting generic date values
  latest_date = session.query(measurement_t.date).order_by(measurement_t.date.desc()).first()[0]
  session.close()

  last_datapoint = latest_date.split("-")
  y = int(last_datapoint[0])
  m = int(last_datapoint[1])
  d = int(last_datapoint[2])
  last_datapoint = dt.date(y, m, d)
  first_datapoint = last_datapoint - relativedelta(years=1)

  # Jsonifying on precipitation page
  if current_route in available_routes and current_route == "precipitation":
    session = Session(engine)
    date_vs_prcp = session.query(measurement_t.date, measurement_t.prcp).filter(measurement_t.date >= first_datapoint).all()
    session.close()
    # Create a dictionary and jsonify
    precipitation_dict = [{i[0] : i[1]} for i in date_vs_prcp]
    precipitation_dict_json = jsonify(precipitation_dict)

    return precipitation_dict_json

  # Jsonifying on stations page
  elif current_route in available_routes and current_route == "stations":
    session = Session(engine)
    all_station_data = session.query(station_t.id, station_t.station, station_t.name, station_t.latitude, station_t.longitude, station_t.elevation).all()
    session.close()

    # Create a dictionary and jsonify
    all_station_list = []
    for id, station, name, latitude, longitude, elevation in all_station_data:
      all_station_data = {}
      all_station_data["id"] = id
      all_station_data["station"] = station
      all_station_data["name"] = name
      all_station_data["latitude"] = latitude
      all_station_data["longitude"] = longitude
      all_station_data["elevation"] = elevation
      all_station_list.append(all_station_data)
    stations_dict_json = jsonify(all_station_list)
    
    return stations_dict_json
       
  # Jsonifying on tobs page
  elif current_route in available_routes and current_route == "tobs":
    session = Session(engine)
    most_active_stations = session.query(measurement_t.station, station_t.name, func.count(station_t.id).label("observation_counts")).group_by(station_t.id).order_by(func.count(station_t.id).desc()).filter(station_t.station == measurement_t.station).all()
    session.close()

    # Create a dictionary and jsonify
    tobs_list = []
    for station, name, observation_counts in most_active_stations:
      tobs_data = {}
      tobs_data["station"] = station
      tobs_data["name"] = name
      tobs_data["observation_counts"] = observation_counts
      tobs_list.append(tobs_data)
    tobs_dict_json = jsonify(tobs_list)

    return tobs_dict_json

  # Extracting date range summary temperature values
  elif current_route not in available_routes:
    html = '''<main style="width: 960px; margin: 0 auto">'''
    html += '''<a style="text-decoration: none; color: #008ef6; font-family: system-ui; font-size: 1.5em;" href="/">HOME |</a>'''
    
    # Assigning summary values to a variable
    sel = [func.min(measurement_t.tobs),
       func.max(measurement_t.tobs),
       func.avg(measurement_t.tobs)]

    # Splitting route url extension into maximum of 2 by "/"
    current_route = current_route.split("/")
    # Assign first index value to start
    start = current_route[0]
    session = Session(engine)
    # If more than 1 value after split, assign the second index value to 'end' and query both
    if len(current_route) > 1:
      end = current_route[1]
      search_by_date = session.query(*sel).filter(measurement_t.date >= start).filter(measurement_t.date <= end).all()
      date_range = f"<span>{start} to {end}</span>"
    # Else query only start date
    else:
      search_by_date = session.query(*sel).filter(measurement_t.date >= start).all()
      date_range = f"<span>{start}</span>"

    session.close()

    # Displaying the summary min, max and avg temperatures
    html+="<article>"
    html+=f'''
    <h2 style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 1.8em; font-weight: lighter">Lowest, Highest, and Avg temperatures from {date_range}</h2>
    <ul style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 1.4em; font-weight: lighter;">
    <li>Lowest Temperature:   {search_by_date[0][0]}</li>
    <li>Highest Temperature: {search_by_date[0][1]}</li>
    <li>Average Temperature:  {search_by_date[0][2]}</li>
    </ul>
    '''
    html+="</article>"
    html += "</main>"

    return html

if __name__ == '__main__':
    app.run()