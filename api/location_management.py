from .CONSTANTS import LOCATION_INFO, MENU_REQUEST, SCHEDULE_REQUEST, MEAL_TO_PERIOD
import requests
import bs4
from bs4 import BeautifulSoup as bs
from .helpers import normalize_time_from_str, parse_date, get_irvine_time, get_date_str

def is_valid_location(location: str) -> bool:
    'Check if the location is valid'
    if location in LOCATION_INFO:
        return True
    return False

def get_name(location: str):
    'Assuming valid location is provided, return the official name for diner'
    return LOCATION_INFO[location]['official']

def get_id(location: str) -> int:
    'Assuming valid location is provided, return id for diner'
    return LOCATION_INFO[location]['id']

def get_menu_data(location, meal_id, date):
    '''
    Given a valid location, meal_id, and date,
    perform get request for the diner_json and return the dict at diner_json['Menu']
    '''
    print(MENU_REQUEST(
                location_param  = get_id(location), 
                meal_param      = MEAL_TO_PERIOD[meal_id][0],
                date_param      = date))
    response = requests.get(
            MENU_REQUEST(
                location_param  = get_id(location), 
                meal_param      = MEAL_TO_PERIOD[meal_id][0],
                date_param      = date)
            )
    if response.status_code==200:
        payload = response.json()
        if 'Menu' in payload:
            return payload['Menu']
        else:
            raise KeyError(f'Key "Menu" not found in campusdish response object. Response payload below:\n{payload}')
    else:
        response.raise_for_status()

def get_schedule_data(location, date):
    '''
    Given a valid location and date,
    perform get request for the schedule_json
    '''
    return requests.get(
            SCHEDULE_REQUEST(
                location_param  = get_id(location), 
                date_param      = date)
            ).json()['Result']

def get_event_data(restaurant: str) -> list[dict]:
    '''
    Given a valid location and date,
    perform get request, then parse the HTML code for the event_json using BeautifulSoup 4
    '''
    url = 'https://uci.campusdish.com/LocationsAndMenus/'
    if restaurant == 'Anteatery':
        url += 'TheAnteatery'
    else:
        url += restaurant

    soup = bs(requests.get(url).text, 'html.parser')
    table_rows = soup.find_all('tr', attrs={"style":"height: 10pt;"})

    def event_from_soup(soup_object: bs4.element.Tag):
        text_list = [td.getText().strip() for td in soup_object.find_all("td")]
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
    return list(filter(None, (event_from_soup(row) for row in table_rows)))