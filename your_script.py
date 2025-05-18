import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import streamlit as st

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

try:
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"❌ Google credentials error: {e}")
    st.stop()

sheet_file = 'Swamp House Topic Scraper'

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

def job():
    today = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
    st.write(f"\n🕕 Starting scrape job at {today}")
    all_rows = []

    for site_name, url in news_sites.items():
        st.write(f"\n🔍 Scraping: {site_name}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Site-specific headline selectors
            if site_name == 'Gateway Pundit':
                articles = soup.select('h2.entry-title a')
            elif site_name == 'Breitbart':
                articles = soup.select('div.bndn-hdln a, h2 a')
            elif site_name == 'Townhall':
                articles = soup.select('section.content a')
            elif site_name == 'Fox News':
                articles = soup.select('h2.title a, h4.title a')
            elif site_name == 'New York Post':
                articles = soup.select('h3.entry-heading a, h2.headline a')
            else:
                articles = soup.find_all('a')

            st.write(f"✅ Found {len(articles)} potential headlines in {site_name}")

            worksheet = client.open(sheet_file).worksheet(site_name)
            worksheet.clear()
            worksheet.append_row(['Date', 'Headline', 'Link'])

            added = set()
            rows = []

            for a in articles:
                href = a.get('href')
                text = a.get_text(strip=True)

                if not href or not text:
                    continue

                # Build full URL if needed
                if not href.startswith('http'):
                    full_url = url.rstrip('/') + '/' + href.lstrip('/')
                else:
                    full_url = href

                # Check that it's a valid article link and not duplicate text
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

# Add button to trigger scraping
if st.button("Start Scraping"):
    data = job()

    if data:
        st.write("Scraped Data:")
        st.write(data)  # Display the scraped headlines
    else:
        st.write("No data to display.")
