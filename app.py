from flask import Flask, session, request, redirect, url_for, render_template
from os import urandom
from dotenv import dotenv_values
from station import RealFm, Parapolitika
from server import Server

app = Flask(__name__)

app.debug = True
app.secret_key = urandom(24)


@app.route("/", methods=['GET','POST'])
def check_user():
    if 'username' in session:
        return redirect(url_for('stations'))
    else:
        if request.method == 'POST':
            if request.form['password'] == "123":
                session['username'] = "dimitris"
                return redirect(url_for('stations'))
            else:
                return render_template("index.html")
        else:
            return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('check_user'))


@app.route("/stations")
def stations():
    if 'username' in session:
        for stat in stations:
            stat.reset()
        supported_stations = [stat.title for stat in stations]
        return render_template('stations.html',
                               user=session['username'],
                               stations=supported_stations)
    else:
        return redirect(url_for('check_user'))

@app.route("/shows", methods=['GET', 'POST'])
def shows():
    if 'username' in session:
        if request.method == "POST":
            stat_ind = []
            for station_wanted in request.form:
                stations[int(station_wanted[0])].select()
                stat_ind.append(int(station_wanted[0]))
            wanted_stations = [station for station in stations if station.selected]
            return render_template('shows.html', stations=wanted_stations)
        else:
            return redirect(url_for("check_user"))
    else:
        return redirect(url_for('check_user'))


@app.route("/dates", methods=['GET','POST'])
def dates():
    if 'username' in session:
        if request.method == "POST":
            the_form = request.form
            for show_wanted in request.form:
                station_index=int(show_wanted.split(":")[0])
                show_index = int(show_wanted.split(":")[1])
                stations[station_index].shows[show_index].select()
            return render_template('dates.html', stations=stations)
        else:
            return redirect(url_for('check_user'))
    else:
        return redirect(url_for('check_user'))

@app.route('/download', methods=['GET','POST'])
def download():
    if 'username' in session:
        if request.method == "POST":
            for day_wanted in request.form:
                station_index=int(day_wanted.split(":")[0])
                show_index = int(day_wanted.split(":")[1])
                day_index = int(day_wanted.split(":")[2])
                stations[station_index].shows[show_index].archive.days[day_index].select()
            pull_and_push()
            return render_template('download.html')
        else:
            return redirect(url_for('check_user'))
    else:
        return redirect(url_for('check_user'))


def pull_and_push():
    for station in stations:
        if station.selected:
            wanted_days = station.get_selected_days()
            for day in wanted_days:
                day.print()
            if len(wanted_days) > 0:
                print("####### PULLING STREAMS #######")
                server.pull(wanted_days)
                print("####### PULSHING STREAMS #######")
                server.push(wanted_days)
                print("####### DELETING LOCALS #######")
                server.delete_locals(wanted_days)


if __name__ == "__main__":
    # Load the environment variables from .env
    env_vars = dotenv_values('.env')

    # Access the environment variables
    temp_folder = env_vars['TEMP']
    final_folder = env_vars['TARGET']

    stations = [RealFm("https://www.real.gr/realfm/"),
                Parapolitika("https://dromos.ddns.net")]
    server = Server(temp_folder,final_folder)
    app.run(debug=True, port=5000, host='0.0.0.0')




