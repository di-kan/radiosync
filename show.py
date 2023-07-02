import re
from file import File
from datetime import datetime
from utils import get_soup


class ADay:
    def __init__(self, url, description, date):
        """Initialize attributes"""
        self.url = url
        self.files = []
        self.date = date
        self.description = description
        self.selected = False
        self.final_file = None

    def select(self):
        self.selected = True
        soup = get_soup(self.url)
        the_files = soup.select(".captionmedia a")
        self.files = [File(file['href']) for file in the_files]

    def get_all_filenames(self):
        ret_value = ""
        for file in self.files:
            ret_value += f"'{file.local_path}{file.filename}' "
        ret_value +=  f"'{self.final_file.local_path}{self.final_file.filename}' "
        return ret_value

    def print(self):
        print(f"|{self.date}|{self.selected}|{self.description}|{self.url}|")
        for file in self.files:
            file.print()


class Archive:
    def __init__(self, show, archive_list):
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
            self.days.append(ADay(day_url, description, the_date))



class Show:
    def __init__(self, station, start_url, persons, logo_url):
        self.persons = persons
        self.logo_url = logo_url
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
        archive = self._soup.select(".ddown option")
        archive_list = [ {"desc":arch.getText(), "url":f"https://www.real.gr{arch['value']}"} for arch in archive[1:]]
        self.archive = Archive(self, archive_list)

    def get_archive_list(self):
        return [f"{day.description}" for day in self.archive.days]

    def print(self):
        print(f"\t{self.persons}\t{self.logo_url}")