# Historical Data Downloder
## Description
This is a historical data downloader for [Hist Data](https://histdata.com). It will scrape the page, download the data, and merge it all into one csv. It is very simple implementation. I could have just downloaded everything by hand.... but thats not as fun :)

### Usage 
Clone the repository and run `python3 main.py`. This will create a folder called `downloaded_tickers` which will contain all of data that has been downloaded. Add the symbol you would like to download to `tickers_to_download` in `main.py`.

### Future plans that I would not like to do right now?
- make it asynchronous instead?
- add command line parsing?
- make it so you can give a date range?
