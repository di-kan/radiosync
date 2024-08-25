from abc import ABC, abstractmethod
from show import Show
from utils import get_soup
import json
import requests
import music_tag
from tqdm import tqdm
from subprocess import call
from urllib.parse import urlparse, unquote
import re
import os
from file import File
from yt_dlp import YoutubeDL
from time import sleep


class Station(ABC):
    def __init__(self):
        self.shows = []
        self.selected = False
        self.title = ''

    def select(self):
        self.selected = True
        disconnected = True
        while disconnected:
            try:
                self._soup = get_soup(self.start_url)
            except Exception as e:
                print(e)
                print("sleeping for 10s")
                sleep(10)
            else:
                disconnected=False
        self.scan()

    def get_shows_list(self):
        return [show.persons for show in self.shows]

    @abstractmethod
    def scan(self):
        pass

    def get_selected_days(self):
        selected_days = []
        for show in self.shows:
            if show.selected:
                for day in show.archive.days:
                    if day.selected:
                        selected_days.append(day)
        return selected_days

    @abstractmethod
    def get_show_archive_list(self):
        pass

    @abstractmethod
    def get_day_files(self):
        pass

    @abstractmethod
    def print(self):
        pass

    @abstractmethod
    def downloader(self):
        pass

    @abstractmethod
    def reset(self):
        print("Station is reset")

class RealFm(Station):
    def __init__(self, start_url="https://www.real.gr/realfm/"):
        super().__init__()
        self.title = 'Real FM'
        self.start_url = start_url        

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

    def print(self):
        for show in self.shows:
            show.print()

    def downloader(self, day, pull_path):
        def _save(a_file):
            resume_byte_pos = 0
            the_file = f"{pull_path}{a_file.filename}"
            if os.path.exists(the_file):
                resume_byte_pos = os.path.getsize(the_file)
            headers = {"Range":f"bytes={resume_byte_pos}-"}
            response = requests.get(a_file.url, headers=headers, stream=True)
            total_size = int(response.headers.get('content-length', 0)) + resume_byte_pos
            block_size = 1024  # 1 KB
            progress_bar = tqdm(total=total_size,
                                desc=a_file.filename,
                                unit='B',
                                initial=resume_byte_pos,
                                unit_scale=True,
                                colour='BLUE')

            with open(the_file, 'ab') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()

        def _concat_files(day):
            final_filename = f"{day.description.replace('/','_')}.mp3"
            if len(day.files) > 1:
                ffmpeg_concat_string = "ffmpeg -hide_banner -loglevel error -y -i 'concat:"
                for file in day.files:
                    ffmpeg_concat_string += f"{pull_path}{file.filename}|"
                ffmpeg_concat_string = ffmpeg_concat_string[:-1]
                ffmpeg_concat_string += f"' -acodec copy '{pull_path}{final_filename}'"
                call(ffmpeg_concat_string, shell=True)
            else:
                src = f"{pull_path}{final_filename}"
                cp_command = f"rsync -v '{src}' '{pull_path}'"
                call(cp_command, shell=True)
            print("--------------------------------")
            return final_filename

        def _apply_tags(day):
            # Apply new mp3 tags
            the_file = music_tag.load_file(f"{pull_path}{day.final_file.filename}")
            the_file['artist'] = day.show.persons
            the_file['title'] = day.description
            the_file['album'] = day.show.station.title
            # set artwork
            _save(day.show.logo)
            img_file = f"{pull_path}{day.show.logo.filename}"
            with open(img_file, 'rb') as img_in:
                the_file['artwork'] = img_in.read()
            the_file['artwork'].first.thumbnail([64, 64])
            the_file['artwork'].first.raw_thumbnail([64, 64])
            the_file.save()

        for a_file in day.files:
            _save(a_file)
        final_filename = _concat_files(day)
        day.final_file = File(filename=final_filename)
        _apply_tags(day)

    def get_show_archive_list(self, soup):
        archive = soup.select(".ddown option")
        return [{"desc":arch.getText(), "url":f"https://www.real.gr{arch['value']}"} for arch in archive[1:]]

    def get_day_files(self, day):
        soup = get_soup(day.url)
        the_files = soup.select(".captionmedia a")
        result = []
        for a_file in the_files:
            fname = os.path.basename(urlparse(a_file['href']).path)
            url = a_file['href']
            result.append(File(url, fname))
        return result

    def reset(self):
        super().reset()
        self.shows = []
        self.selected = False
        self.title = 'Real FM'

class Parapolitika(Station):
    def __init__(self, start_url="https://www.parapolitika.gr/parapolitikafm/"):
        super().__init__()
        self.start_url = start_url
        self.shows = []
        self.title = "Παραπολιτικά"

    def scan(self):
        """Scans the website and populates the list of Shows"""
        print(f"Scanning {self.title} website for shows available")
        all_shows = self._soup.find_all("div", class_="radioBroadcast")
        urls =  [f'https://www.parapolitika.gr{a_show.find("a")["href"]}' for a_show in all_shows]
        persons_dict = {urls[index]:a_show.find('span', class_="radioProducers").text for index, a_show in enumerate(all_shows)}
        urls = list({url for url in urls})
        persons = [persons_dict[url] for url in urls]
        logos = ['"https://s.parapolitika.gr/assets/Media/logo.svg"' for _ in urls]

        for i in range(0, len(urls)):
            self.shows.append(Show(self, urls[i], persons[i], logos[i]))

    def get_show_archive_list(self, soup):
        frames = soup.find_all("iframe")
        archive = []
        for frame in frames:
            url = unquote(frame['src'], encoding='utf-8', errors='replace')
            url = re.sub("widget.*feed=/", "", url)
            desc = url.split("/")[-2].split("-")
            date = "/".join(desc[-3:])
            desc = " ".join(desc[0:-3]).replace("-", " ").title()
            archive.append({"desc":f"{date} {desc}", "url":url})
        return archive

    def get_day_files(self, day):
        url = f"{day.url}"
        return [File(url=url, filename=f"{day.description}.opus")]

    def downloader(self, day, pull_path):
        def _save(day_file):
            output_template = '%(title)s.%(ext)s'  # Template to specify the output filename
            ydl_opts = {
                'outtmpl': output_template,  # Set the output template for filename
                'verbose': False,
                'paths': {'home':pull_path},
                'continuedl': True,
                'concurrent_fragment_downloads': 4,
                'quiet': True,
                'no_warnings': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info_dict = ydl.extract_info(day_file.url, download=False)  # Extract video info
                    filename = ydl.prepare_filename(info_dict)  # Generate the filename
                    ydl.download(day_file.url)  # Download the video
                except Exception:
                    print("Error")
            return filename

        def _normalize(fname):
            fname = fname.split("/")[2]
            date = fname.split(" ")[-1].split('.')[0].replace("-", "_")
            desc = fname.split(" ")[0:-1]
            desc = " ".join(desc).title()
            ext = fname.split(".")[-1]
            # print(f"{fname} --> {date} | {desc} | {ext}")
            new_fname = f"{date} {desc}.{ext}"
            if os.path.exists(f"{pull_path}{fname}") and os.path.isfile(f"{pull_path}{fname}"):
                os.rename(src=f"{pull_path}{fname}", dst=f"{pull_path}{new_fname}")
            return new_fname

        fname = _save(day.files[0])
        day.final_file = File(filename=_normalize(fname))

    def print(self):
        print(f"{self.name} Contents:")

    def reset(self):
        super().reset()
        self.shows = []
        self.selected = False
        self.title = 'Parapolitika'
