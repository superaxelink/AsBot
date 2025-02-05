import pytest
import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)
from DownloadFile.webscraper import *


def test_webscraper():
  download_directory = "test_download"
  page = "envato"
  scraper = Webscraper(download_directory, page)

  

