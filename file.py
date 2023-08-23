import os
from urllib.parse import urlparse


class File:
    def __init__(self, url='', filename =''):
        self.url = url
        self.filename = filename

    def print(self):
        print("|".join([self.url, self.filename]))
