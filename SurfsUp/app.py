from flask import Flask, jsonify

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
from dateutil.relativedelta import relativedelta

# Setting Up the Database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(autoload_with=engine)

# Saving references to the db tables
measurement_t = Base.classes.measurement
station_t = Base.classes.station

available_routes = ['precipitation', 'stations', 'tobs']

app = Flask(__name__)

@app.route('/')
def index():
  html = '''<main style="width: 960px; margin: 0 auto">'''
  html += f'''
  <a style="text-decoration: none; color: #008ef6; font-family: system-ui; font-size: 1.5em;" href="/">HOME |</a>
  <h1 style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 2em; font-weight: lighter">List of all available routes</h1>
  '''
  html+='''<ul style="text-decoration: none;font-family: system-ui; font-size: 1.4em; font-weight: lighter">'''
  for li in available_routes:
    # html+=f'''<li style="list-style: none;"><a style="text-decoration: none; color: #008ef6;" href='/api/v1.0/{li}'</a> {li.title()}</li>'''
    html+=f'''<li style="list-style: none;"> <a style="text-decoration: none; color: #008ef6;" href="/api/v1.0/{li}">{li.title()}</a> </li>'''
  html+="</ul>"
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

    precipitation_dict = [{i[0] : i[1]} for i in date_vs_prcp]
    precipitation_dict_json = jsonify(precipitation_dict)

    return precipitation_dict_json

  # Jsonifying on stations page
  elif current_route in available_routes and current_route == "stations":
    session = Session(engine)
    all_station_data = session.query(station_t.id, station_t.station, station_t.name, station_t.latitude, station_t.longitude, station_t.elevation).all()
    session.close()
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
    html += '''<a style="list-style: none;"><a style="text-decoration: none; color: #008ef6; font-family: system-ui; font-size: 1.5em;" href="/">HOME |</a>
  <h1 style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 2em; font-weight: lighter">List of all available routes</h1>
  '''
    sel = [func.min(measurement_t.tobs),
       func.max(measurement_t.tobs),
       func.avg(measurement_t.tobs)]
       
    current_route = current_route.split("/")
    start = current_route[0]
    session = Session(engine)

    if len(current_route) > 1:
      end = current_route[1]
      search_by_date = session.query(*sel).filter(measurement_t.date >= start).filter(measurement_t.date <= end).all()
      date_range = f"<span>{start} to {end}</span>"
    else:
      search_by_date = session.query(*sel).filter(measurement_t.date >= start).all()
      date_range = f"<span>{start}</span>"


    session.close()
    html+="<article>"
    html+=f'''
    <h2 style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 1.7em; font-weight: lighter">Lowest, Highest, and Average temperatures from {date_range}</h2>
    <ul style="text-decoration: none; color: #3c3b3b; font-family: system-ui; font-size: 1.4em; font-weight: lighter;">
    <li>Lowest Temperature:   {search_by_date[0][0]}</li>
    <li>Highest Temperature: {search_by_date[0][1]}</li>
    <li>Average Temperature:  {search_by_date[0][2]}</li>
    </ul>
    '''
    # if search_by_date[0][0] == "none" or not search_by_date[0][0]
    html+="</article>"
    html += "</main>"


    return html


if __name__ == "__main__":
    app.run(debug=True)