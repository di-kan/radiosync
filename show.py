import re
import os
from urllib.parse import urlparse
from file import File
from datetime import datetime
from utils import get_soup


class ADay:
    def __init__(self, the_show, url, description, date, station):
        """Initialize attributes"""
        self.station = station
        self.downloader = station.downloader
        self.show = the_show
        self.url = url
        self.files = []
        self.date = date
        self.description = description
        self.selected = False
        self.final_file = None

    def select(self):
        self.selected = True
        the_files = self.station.get_day_files(self)
        self.files = the_files

    def get_all_filenames(self):
        all_filenames = [a_file.filename for a_file in self.files]
        all_filenames.append(self.show.logo.filename)
        return all_filenames

    def print(self):
        print(f"|{self.date}|{self.selected}|{self.description}|{self.url}|")
        for file in self.files:
            file.print()


class Archive:
    def __init__(self, show, archive_list, station):
        self.station = station
        self.show = show
        # list of ADay
        self.days = []
        self.populate(archive_list)

    def print(self):
        print(f'Archive:{[f"{str(dt.date)}," for dt in self.days]}')


    def populate(self, archive_list):
        for show in archive_list:
            the_date_str = show['desc'].split(' ')[0]
            the_date_str = re.sub(r'[^0-9/]','',the_date_str)
            the_date = datetime.strptime(the_date_str, "%d/%m/%Y").date()
            day_url = show['url']
            description = show['desc']
            self.days.append(ADay(self.show, day_url, description, the_date, self.station))


class Show:
    def __init__(self, station, start_url, persons, logo_url):
        self.persons = persons
        self.logo = File(url=logo_url, filename=os.path.basename(urlparse(logo_url).path))
        self.url = start_url
        self.station = station
        self.selected = False
        #archive won't populate yet. Only if show is selected later
        self.archive = None
        self._soup = ""

    def select(self):
        print(f"{self.persons} was selected. Populating archive...")
        self.selected = True
        self._soup = get_soup(self.url)
        archive_list = self.station.get_show_archive_list(self._soup)
        self.archive = Archive(self, archive_list, self.station)

    def get_show_archive_list(self):
        return [f"{day.description}" for day in self.archive.days]

    def print(self):
        print(f"\t{self.persons}\t{self.logo_url}")