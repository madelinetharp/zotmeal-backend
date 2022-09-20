import re
import traceback
import requests
import bs4
import json
from bs4 import BeautifulSoup as bs
from .util import normalize_time_from_str, parse_date, get_irvine_time, get_date_str, get_website_location_name, EVENTS_PLACEHOLDER

def get_menu_data(location, meal_id, date):
    '''
    Given a valid location, meal_id, and date,
    perform get request for the diner_json and return the dict at diner_json['Menu']
    '''

    url = f'https://uci.campusdish.com/en/LocationsAndMenus/{get_website_location_name(location)}'

    response = requests.get(
        url
    )
    if response.status_code==200:
        raw_html_text_body = response.text
        obj_match = re.search(r"model: (.*)", raw_html_text_body)
        return json.loads(obj_match.group(1))["Menu"]
        
    else:
        print("Response error message: ", response.json())
        response.raise_for_status()

def get_schedule_data(location, date):
    '''
    Given a valid location and date,
    perform get request for the schedule_json
    '''
    response = requests.get(
        f'https://uci.campusdish.com/api/menu/GetMenuPeriods?locationId={location}&date={date}'
    )
    if response.status_code==200:
        return response.json()['Result']
    else:
        print("Response error message: ", response.json())
        response.raise_for_status()

def get_themed_event_data(restaurant: str) -> list[dict]:
    '''
    Given a valid location and date,
    perform get request, then parse the HTML code for the event_json using BeautifulSoup 4
    '''
    url = 'https://uci.campusdish.com/LocationsAndMenus/'
    if restaurant == 'Anteatery':
        url += 'TheAnteatery'
    else:
        url += restaurant

    try:
        soup = bs(requests.get(url).text, 'html.parser')
        table_rows = soup.find_all('tr', attrs={"style":"height: 10pt;"})

        def event_from_soup(soup_object: bs4.element.Tag):
            text_list = [td.getText().strip() for td in soup_object.find_all("td")]
            try:
                event_date = parse_date(text_list[0])
                if event_date<get_irvine_time():
                    return False

                start_time, end_time = map(normalize_time_from_str, text_list[3].split(' – '))# Warning: this is a weird character. The character U+2013 "–" could be confused with the character U+002d "-", which is more common in source code. UCI uses this weird character in their website for some reason, but if they change it to a normal hyphen this will break.
                return {
                    'date':get_date_str(event_date),
                    'name':text_list[1],
                    'service_start':start_time,
                    'service_end':end_time
                }
            except Exception as e:
                traceback.print_exc()
        return list(filter(None, (event_from_soup(row) for row in table_rows)))
    except:
        return EVENTS_PLACEHOLDER