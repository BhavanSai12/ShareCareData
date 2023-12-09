import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from openpyxl import load_workbook
from collections import defaultdict
import time
import sys

def generate_search_url(city, state, page_number):
    base_url = "https://www.sharecare.com/find-a-doctor/search"
    location = f"?what=Dentistry&where={city}%2C+{state}"
    return f"{base_url}{location}&pageNum={page_number}"

def extract_doctor_urls(page_url, base_sharecare_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')
    doctor_urls = {base_sharecare_url + link.get('href') for link in links if link.get('href') and "/doctor/" in link.get('href')}
    return list(doctor_urls)

def parse_full_name(full_name):
    name_titles = ["BDS", "BDent", "BDSc", "BScD", 
                   "BM", "MS", "MSc", "MSD", "MMSc", 
                   "MDent", "MDS", "MDentSci", "MS", "MCS", 
                   "MSM", "DDS", "DMD", "DClinDent", "DDSc", 
                   "DScD", "DMSc", "DDent", "PhD", "Dr.", 
                   "Jr", "Sr", "I", "II", "III", "IV", "V"]
    # Split the name into words
    name_words = full_name.split()
    name_words_parsed = []
    pattern = r'[.,]'

    for name_word in name_words:
        space_stripped = name_word.strip()
        if space_stripped[-1] == ',':
            comma_stripped = re.sub(pattern, '', space_stripped)
            name_words_parsed.append(comma_stripped)
        else:
            name_words_parsed.append(space_stripped)

    # Check if any word is a dental title
    names = []
    for i in range(len(name_words_parsed)):
        if name_words_parsed[i] in name_titles:
            # If found, remove it from the name
            continue
        else:
            names.append(name_words_parsed[i])

    if len(names) == 3:
        return names[0], names[1], names[2]
    elif len(names) == 2:
        return names[0], "", names[1]
    elif len(names) == 1:
        return names[0], "", ""
    else:
        print(f"Unable to parse full name: {full_name}")
        return "", "", ""
   
def parse_address(full_address):
    # Initialize components with empty strings
    street, city, state_code, zipcode = "", "", "", ""

    # Try to extract components from the full address
    try:
        address_parts = full_address.split(",")
        if len(address_parts) >= 1:
            street = address_parts[0].strip()
        if len(address_parts) >= 2:
            city = address_parts[1].strip()
        if len(address_parts) >= 3:
            state_zip_parts = address_parts[2].split()
            if len(state_zip_parts) >= 1:
                state_code = state_zip_parts[0].strip()
            if len(state_zip_parts) >= 2:
                zipcode = state_zip_parts[1].strip()
    except Exception as e:
        print(f"Error parsing address: {e}")

    return [street, city, state_code, zipcode]

def web_scrapping(url):
    provider_details = defaultdict(list)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Name
    name_div = soup.find('div', class_='ProviderLeadStyleTwo-title')
    full_name_div = name_div.get_text()
    full_name = re.sub(r'\n', '', full_name_div)
    first_name, middle_name, last_name = parse_full_name(full_name)
    provider_details['full_name'].append(full_name)
    provider_details['name'] = [first_name, middle_name, last_name]

    # Insurance details
    insurance_provider_details = defaultdict(list)
    ul = soup.find('ul', {'class': 'ProviderInsuranceAccepted-description'})
    if ul:
        for li in ul.find_all('li'):
            label = li.find('label')
            article = li.find('article')
            if article:
                divs = article.find_all('div')
                for div in divs:
                    insurance_provider_details[label.text].append(div.text)
            else:
                insurance_provider_details[label.text] = {}
    provider_details['insurances_accepted'] = insurance_provider_details

    # Location
    addresses = []
    address_spans = soup.find_all('address')
    for address_span in address_spans:
        a_spans = address_span.find_all('span')
        address = a_spans[1].text
        addresses.append(parse_address(address))
    provider_details['addresses'] = addresses

    # Specialities
    specialities = []
    specialities_divs = soup.find_all('div', {'class': 'ProviderAboutStatsItem-list-box-item'})
    for specialities_div in specialities_divs:
        speciality = re.sub(r'\n', '', specialities_div.get_text())
        specialities.append(speciality.strip())
    provider_details['specialities'] = specialities

    # Phone number
    phone_numbers = []
    alternate_detail_divs = soup.find_all('div', {'class', 'ProviderLocationsModuleAlternative-buttons'})
    for alt_det_div in alternate_detail_divs:
        tel_tag = alt_det_div.find('a', {'data-analytics': 'make-appointment__phone--existing', 'data-phone': ''})
        if tel_tag:
            tel_phone_number = tel_tag.get('href', '')
            phone_number = re.sub("tel:", "", tel_phone_number)
            phone_numbers.append(phone_number)
    provider_details['phone_numbers'] = phone_numbers

    return provider_details

def get_provider_details(urls, start_index=0):
    rows = []
    for i, url in enumerate(urls[start_index:], start=start_index):
        try:
            provider_details = web_scrapping(url)
            row = []
            row.extend(provider_details['full_name'])
            full, middle, last = provider_details['name']
            row.extend([full, middle, last])
            row.extend([provider_details['addresses']])
            row.extend([provider_details['specialities']])
            row.extend([provider_details['phone_numbers']])
            row.extend([provider_details['insurances_accepted']])
            rows.append(row)
        except Exception as e:
            print(f"Error processing URL {i + 1}: {e}")
            # Save the current state to a file
            save_state(i + start_index + 1, urls)
            sys.exit(1)

    df = pd.DataFrame(rows, columns=['full_name', 'first_name', 'middle_name', 'last_name',
                                    'addresses', 'specialities', 'phone_numbers',
                                    'insurances_accepted'])

    excel_file = 'sharecare_detail.xlsx'
    print('Completed Scrapping!')
    # Check if the file exists, and create it if not
    if not os.path.isfile(excel_file):
        df.to_excel(excel_file, index=False)
    else:
        print("EXCEL FILE WITH SIMILAR NAME EXISTS")
        exit()

def save_state(current_index, urls):
    state = {'current_index': current_index, 'urls': urls}
    with open('state.json', 'w') as state_file:
        json.dump(state, state_file)

def load_state():
    if os.path.isfile('state.json'):
        with open('state.json', 'r') as state_file:
            return json.load(state_file)
    else:
        return None

def main():
    start_time = time.time()  # Record the start time
    state = load_state()
    if state:
        start_index = state['current_index']
        urls = state['urls']
        print(f"Resuming from URL {start_index + 1}")
    else:
        start_index = 0
        # Load JSON data from the file
        json_file_path = r"USA.json"
        with open(json_file_path, 'r') as json_file:
            states_and_cities = json.load(json_file)

        # Initialize variables
        base_sharecare_url = "https://www.sharecare.com"
        all_doctor_urls = []

        # Iterate through states and cities
        for state, cities in states_and_cities.items():
            for city in cities:
                # Iterate through pages 1 to 99
                for page_number in range(1, 100):
                    page_url = generate_search_url(city, state, page_number)
                    current_page_doctor_urls = extract_doctor_urls(page_url, base_sharecare_url)

                    # If no doctor URLs are found on the current page, break out of the loop
                    if not current_page_doctor_urls:
                        break

                    all_doctor_urls.extend(current_page_doctor_urls)

        # Create a DataFrame using pandas
        df_urls = pd.DataFrame({'urls': all_doctor_urls})

        # Remove duplicates from the DataFrame
        df_urls.drop_duplicates(subset='urls', inplace=True)
        urls = [url.strip() for url in df_urls['urls'].tolist()]

    # Start data extraction
    get_provider_details(urls, start_index)

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time
    print(f"Total processing time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()
