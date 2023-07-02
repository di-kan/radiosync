import os
from urllib.parse import urlparse


class File:
    def __init__(self, url='', local_path=''):
        self.url = url
        self.filename = self._find_filename()
        self.local_path = local_path

    def _find_filename(self):
        return os.path.basename(urlparse(self.url).path)

    def print(self):
        print(f"{self.url}|{self.filename}|{self.local_path}|")

