import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import streamlit as st

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '1-NX22kxDlDLLnoxhaXboo9MRQDLLdD9Qf7CgW1weYBI'
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)

# News sources and worksheet mapping
news_sites = {
    'Gateway Pundit': 'https://www.thegatewaypundit.com/',
    'Breitbart': 'https://www.breitbart.com/',
    'Townhall': 'https://townhall.com/',
    'Fox News': 'https://www.foxnews.com/',
    'New York Post': 'https://nypost.com/',
}

# Common headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

# Streamlit UI
st.title("News Scraper")
st.write("Click the button below to start scraping the latest headlines.")

# Scraping function
def job():
    today = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
    st.write(f"\n🕕 Starting scrape job at {today}")
    all_rows = []
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    for site_name, url in news_sites.items():
        st.write(f"\n🔍 Scraping: {site_name}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            st.write(f"✅ Found {len(links)} links in {site_name}.")

            worksheet = spreadsheet.worksheet(site_name)
            worksheet.clear()
            worksheet.append_row(['Date', 'Headline', 'Link'])

            added = set()
            rows = []

            for a in links:
                href = a.get('href')
                text = a.get_text(strip=True)

                if not href or not text:
                    continue

                full_url = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                if any(domain in full_url for domain in ['gatewaypundit.com', 'breitbart.com', 'townhall.com', 'foxnews.com', 'nypost.com']) and text not in added:
                    rows.append([today, text, full_url])
                    added.add(text)

            if rows:
                worksheet.append_rows(rows)
                st.write(f"✅ Appended {len(rows)} rows to {site_name}")
                all_rows.extend(rows)
            else:
                st.write("⚠️ No valid headlines found.")

        except Exception as e:
            st.write(f"❌ Error scraping {site_name}: {e}")

    return all_rows

# Button to trigger scrape
if st.button("Start Scraping"):
    data = job()
    if data:
        st.write("Scraped Data:")
        st.write(data)
    else:
        st.write("No data to display.")
