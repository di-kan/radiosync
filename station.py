from abc import ABC, abstractmethod
from show import Show
from utils import get_soup
import json

class Station(ABC):
    def __init__(self):
        self.shows = []
        self.selected = False
        self.title = ''

    def select(self):
        self.selected = True
        self.scan()

    def get_shows_list(self):
        return [show.persons for show in self.shows]

    @abstractmethod
    def scan(self):
        pass

    @abstractmethod
    def print(self):
        pass

    @abstractmethod
    def reset(self):
        print("Station is reset")



class RealFm(Station):
    def __init__(self, start_url):
        super().__init__()
        self.title = 'Real FM'
        self.start_url = start_url
        self._soup = get_soup(start_url)

    def scan(self):
        """Scans the website and populates the list of Shows"""
        print(f"Scanning {self.title} website for shows available")
        all_shows = self._soup\
            .select_one(".audioarchive div.row")\
            .select("div div div div .post-thumb")
        urls =  [f'https://www.real.gr{a_show.select_one("a")["href"]}' for a_show in all_shows]
        persons = [a_show.select_one('img')['title'] for a_show in all_shows]
        logos = [f'https://www.real.gr{a_show.select_one("img")["src"]}' for a_show in all_shows]
        for i in range(0, len(urls)):
            self.shows.append(Show(self, urls[i], persons[i], logos[i]))

    def get_selected_days(self):
        selected_days = []
        for show in self.shows:
            if show.selected:
                for day in show.archive.days:
                    if day.selected:
                        selected_days.append(day)
        return selected_days


    def print(self):
        for show in self.shows:
            show.print()

    def reset(self):
        super().reset()
        self.shows = []
        self.selected = False
        self.title = 'Real FM'

class Parapolitika(Station):
    def __init__(self, start_url):
        super().__init__()
        self.start_url = start_url
        self.shows = []
        self.title = "Παραπολιτικά"

    def scan(self):
        print(f"Scanning {self.title} website for shows available")

    def print(self):
        print(f"{self.name} Contents:")

    def reset(self):
        super().reset()
        self.shows = []
        self.selected = False
        self.title = 'Parapolitika'
