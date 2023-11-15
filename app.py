# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func, inspect
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect = True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
# Flask Routes
@app.route('/')
def home():
    """List all available routes."""
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Precipitation data for the last year<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature observation data for the last year<br/>"
        f"/api/v1.0/start_date - Replace 'start_date' with a date in 'YYYY-MM-DD' format to get min, avg, and max temperatures from that date to the end of the dataset<br/>"
        f"/api/v1.0/start_date/end_date - Replace 'start_date' and 'end_date' with dates in 'YYYY-MM-DD' format to get min, avg, and max temperatures for the specified date range<br/>"
    )

@app.route('/api/v1.0/precipitation')
def precipitation():
    """Return the last year of precipitation data."""
    # Calculate the date one year from the most recent date in the dataset.
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query precipitation data for the last year.
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert the query results to a dictionary.
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route('/api/v1.0/stations')
def stations():
    """Return a list of weather stations."""
    # Query all distinct station names.
    station_names = session.query(Station.station).distinct().all()

    # Convert the query results to a list.
    stations_list = [name for name, in station_names]

    return jsonify(stations_list)

@app.route('/api/v1.0/tobs')
def tobs():
    """Return temperature observation data for the last year from the most active station."""
    # Find the most active station.
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()

    # Extract the station id.
    most_active_station_id = most_active_station[0] if most_active_station else None

    if most_active_station_id:
        # Calculate the date one year from the most recent date in the dataset.
        most_recent_date = session.query(func.max(Measurement.date)).scalar()
        one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

        # Query temperature observation data for the last year from the most active station.
        tobs_data = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == most_active_station_id).\
            filter(Measurement.date >= one_year_ago).all()

        # Convert the query results to a list of dictionaries.
        tobs_list = [{'Date': date, 'Temperature': tobs} for date, tobs in tobs_data]

        return jsonify(tobs_list)
    else:
        return jsonify({"error": "No data found for the most active station."})

@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def temperature_stats(start, end=None):
    """Return temperature statistics for a specified start or start-end range."""
    # Convert start and end dates to datetime objects.
    start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end, '%Y-%m-%d') if end else None

    # Query temperature statistics based on start and end dates.
    if end_date:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).\
            filter(Measurement.date <= end_date).all()
    else:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).all()

    