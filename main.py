import os
import time
import threading
import zipfile
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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

    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Navigate to the website
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Try to close the overlay if possible
    try:
        accept_button = driver.find_element(By.ID, "cookie_action_close_header")  # Update the selector
        accept_button.click()
        time.sleep(1)  # Wait for overlay to close
    except Exception as e:
        print("Could not close overlay:", e)

    # Find the download link and click it
    download_link = driver.find_element(By.ID, "a_file")
    download_link.click()

    # Wait for download to complete
    time.sleep(10) # Adjust this delay as needed

    # Close the browser
    driver.quit()

def process_zip(ticker):
    all_data = []
    for file in sorted(os.listdir(ticker)):
        if file.endswith(".zip"):
            # create the path to the zipfile
            # symbol + name of the zip file
            zip_path = os.path.join(ticker, file)

            # open the zipfile
            with zipfile.ZipFile(zip_path, "r") as z:
                # extract the file
                z.extractall(ticker)

                # go through all of the files 
                for filename in z.namelist():
                    if filename.endswith(".txt"):
                        # remove the text files
                        text_path = os.path.join(ticker, filename)
                        os.remove(text_path)
                    elif filename.endswith(".csv"):
                        # construct the path to the csv
                        csv_path = os.path.join(ticker, filename)

                        # read the csv file to a dataframe and append it to our data
                        df = pd.read_csv(csv_path, sep=";", header = None)
                        df.columns = ['datetime', 'open', 'high', 'low', 'close', 'unused']
                        df = df.drop("unused", axis = 1)
                        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
                        all_data.append(df)

                        # done with the csv, remove it
                        os.remove(csv_path)

            # done with the current zip file, remove it
            os.remove(zip_path)

    # done processing, remove the directory
    os.remove(ticker)
    # merge the dataframes and save it to a csv
    merged_df = pd.concat(all_data)
    merged_df.to_csv(os.path.join("downloaded_tickers", ticker, ticker + "_merged.csv"), index=False, sep=',')


if __name__ == "__main__":

    # the tickers that you want to download, add them to the list 
    tickers_to_download = ["EURUSD", "USDJPY"]

    # get all the tickers and their links
    tickers = get_all_ticker_urls()


    # make downloads directory and directory for the tickers
    if not os.path.exists("downloaded_tickers"):
        os.makedirs("downloaded_tickers")
        for ticker in tickers_to_download:
            ticker_path = os.path.join("downloaded_tickers", ticker)
            if not os.path.exists(ticker_path):
                os.makedirs(ticker_path)

    threads = []
    # get retrieve all the info for our tickers
    for ticker in tickers_to_download:
        url = tickers.loc[ticker, "URL"] # extract the url to for the page containing all of the dates
        ticker_dates = get_ticker_date_urls(url) # retrieve the links for all the dates

        # construct a thread that will download the data for each date
        for index, row in ticker_dates.iterrows():
            url = row["URL"]
            download_thread = threading.Thread(target = download_info, args = (row["URL"], ticker))
            threads.append(download_thread)

    # start and join all threads
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    

    # process the zip files and merge into one big csv
    threads = []
    for ticker in tickers_to_download:
        process_thread = threading.Thread(target = process_zip, args = (ticker,))
        threads.append(process_thread)

    # start and join all threads
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]








