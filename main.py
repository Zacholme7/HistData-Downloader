import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading


def get_all_ticker_urls():
    # send the request
    response = requests.get("https://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes")
    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    # get the table that has all the symbols and get all the link endings
    symbol_table = soup.find_all("table")[0]
    symbol_data = symbol_table.find_all("a")

    # hold all of our symbols and urls
    symbols = []
    urls = []

    for data in symbol_data:
        # get the link ending
        href = data.get("href")

        # add our symbol and url
        symbols.append(href[-6:])
        urls.append("https://www.histdata.com" + href)

    return pd.DataFrame({"URL": urls}, index = symbols)

def get_ticker_date_urls(url):
    # send the request
    response = requests.get(url)

    # Parse the HTML 
    soup = BeautifulSoup(response.text, "html.parser")

    # get all the relevant information
    year_data = soup.find_all("p")[3]
    a_tags = year_data.find_all("a")

    # hold all of our urls and dates
    urls = []
    dates = []

    for tag in a_tags:
        # get the link ending
        href = tag.get("href")

        # all our year and url
        dates.append(href[72:])
        urls.append("https://www.histdata.com" + href)

    return pd.DataFrame({"URL": urls}, index = dates)

def download_info(url, download_dir):
    # Setup Selenium ChromeDriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {
        "profile.default_content_setting_values.cookies": 2,  # Block cookies
        "profile.block_third_party_cookies": True,            # Block third-party cookies
        "download.default_directory": download_dir,# Change this to your desired download directory
        "download.prompt_for_download": False, # To auto download the file without asking
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Navigate to the website
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Find the download link and click it
    download_link = driver.find_element(By.ID, "a_file")
    download_link.click()

    # Wait for download to complete
    time.sleep(5) # Adjust this delay as needed

    # Close the browser
    driver.quit()


if __name__ == "__main__":
    tickers = get_all_ticker_urls()

    ticker = "EURUSD"

    url = tickers.loc[ticker, "URL"]

    dates = get_ticker_date_urls(url)

    download_dir = "/home/zacholme/csStuff/Learning/Algotrading/Misc/HistData/EURUSD"

    threads = []
    for index, row in dates.iterrows():
        url = row["URL"]
        download_thread = threading.Thread(target = download_info, args = (url, download_dir))
        threads.append(download_thread)

    [thread.start() for thread in threads]
    [thread.join() for thread in threads]






