from station import RealFm, Parapolitika
from server import Server
from pick import pick
from utils import clearConsole
from dotenv import dotenv_values


# Load the environment variables from .env
env_vars = dotenv_values('.env')
# Access the environment variables
temp_folder = env_vars['TEMP']
final_folder = env_vars['TARGET']

stations=[RealFm("https://www.real.gr/realfm/"), Parapolitika("https://www.parapolitika.gr/parapolitikafm/")]
server = Server(temp_folder, final_folder)


all_stations = [stat.title for stat in stations]

# for station in stations:
#     station.scan()
#SHOW ALL SUPPORTED STATIONS AND MAKE SELECTION FOR STATIONS TO DOWNLOAD SHOWS FROM
stations_wanted = pick(
    all_stations,
    "Select dates:",
    multiselect=True,
    min_selection_count=0,
    indicator="=>"
)

if stations_wanted:
    for station_wanted in stations_wanted:
        # CREATE THE STATION OBJECT THAT I WANT TO SCRAPE
        station = stations[station_wanted[1]]
        station.select()
        # SHOW LIST OF SHOW/SHOWS AND MAKE SELECTION

        if len(station.get_shows_list()) > 0:
            selected = pick(
                station.get_shows_list(),
                "Select shows:",
                multiselect=True,
                min_selection_count=0,
                indicator="==>"
            )
            shows_wanted = [i[1] for i in selected]
            for show_index in shows_wanted:
                station.shows[show_index].select()

            for show_index in shows_wanted:
                show = station.shows[show_index]
                if len(show.archive.days) > 0 :
                    selected = pick(
                        show.get_show_archive_list(),
                        "Select shows:",
                        multiselect=True,
                        min_selection_count=0,
                        indicator="==>"
                    )
                    days_wanted = [i[1] for i in selected]
                    for day_index in days_wanted:
                        show.archive.days[day_index].select()

        else:
            print(f"No shows for {station.title}")
        clearConsole()

for station in stations:
    if station.selected:
        wanted_days = station.get_selected_days()
        if len(wanted_days)>0 :
            print("####### PULLING STREAMS #######")
            server.pull(wanted_days)
            print("####### PUSHING STREAMS #######")
            server.push(wanted_days, delete=False)
            # print("####### DELETING LOCALS #######")
            # server.delete_locals(wanted_days)