from .CONSTANTS import LOCATION_INFO, MENU_REQUEST, SCHEDULE_REQUEST, MEAL_TO_PERIOD
import requests
from bs4 import BeautifulSoup as bs
from .helpers import normalize_time_from_str, parse_date, get_irvine_time, normalize_time, get_date_str

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
    return requests.get(
            MENU_REQUEST(
                location_param  = get_id(location), 
                meal_param      = MEAL_TO_PERIOD[meal_id][0],
                date_param      = date)
            ).json()['Menu']

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
    # if(restaurant == 'Anteatery'):
    #     url += 'TheAnteatery'
    # else:
    #     url += restaurant
    url += "Brandywine"
    html = requests.get(url).text

    soup = bs(html, 'html.parser')
    table = soup.findAll('td', {'style': ['padding: 0.75pt; border-width: 0.75pt; border-right-style: dashed; border-right-color: #999999; border-bottom-style: dashed; border-bottom-color: #999999; text-align: left;',\
                                        'padding: 0.75pt; border-width: 0.75pt; border-right-style: dashed; border-right-color: #999999; border-bottom-style: dashed; border-bottom-color: #999999; text-align: center;',\
                                        'border-right: 0.75pt dashed #999999; border-bottom: 0.75pt dashed #999999; text-align: left;',\
                                        'padding: 0.75pt; border-right: 0.75pt dashed #999999; text-align: left;',\
                                        'padding: 0.75pt; border-bottom: 0.75pt dashed #999999; text-align: left;']})
    
    entries_list = list(map(lambda element: element.getText().strip('\n'), table))
    rows_list = entries_list[5:]

    curr_time = get_irvine_time()
    event_list = []
    for i in range(0, len(rows_list), 4):
        event_date = parse_date(rows_list[i])
        start_time, end_time = rows_list[i + 3].split(' – ')# Warning: this is a weird character. The character U+2013 "–" could be confused with the character U+002d "-", which is more common in source code. UCI uses this weird character in their website for some reason, but if they change it to a normal hyphen this will break.
        if curr_time>event_date:
            continue
        event_list.append({
            'date': get_date_str(event_date),
            'name': rows_list[i+1],
            'service_start': normalize_time_from_str(start_time),
            'service_end': normalize_time_from_str(end_time)
        })

    return event_list
