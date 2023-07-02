import requests
import os
from bs4 import BeautifulSoup


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def clearConsole():
    command = 'clear'
    os.system(command)
