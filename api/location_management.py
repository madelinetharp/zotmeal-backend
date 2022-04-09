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

<<<<<<< Updated upstream
def get_event_data(restaurant: str) -> dict:
=======
def get_event_data(restaurant: str) -> list[dict]:
    
>>>>>>> Stashed changes
    '''
    Given a valid location and date,
    perform get request, then parse the HTML code for the event_json using BeautifulSoup 4
    '''
    url = 'https://uci.campusdish.com/LocationsAndMenus/'
    if(restaurant == 'Anteatery'):
        url += 'TheAnteatery'
    else:
        url += restaurant
    html = requests.get(url).text

    soup = bs(html, 'html.parser')
    table = soup.findAll('td', {'style': ['padding: 0.75pt; border-width: 0.75pt; border-right-style: dashed; border-right-color: #999999; border-bottom-style: dashed; border-bottom-color: #999999; text-align: left;',\
                                        'padding: 0.75pt; border-width: 0.75pt; border-right-style: dashed; border-right-color: #999999; border-bottom-style: dashed; border-bottom-color: #999999; text-align: center;',\
                                        'border-right: 0.75pt dashed #999999; border-bottom: 0.75pt dashed #999999; text-align: left;',\
                                        'padding: 0.75pt; border-right: 0.75pt dashed #999999; text-align: left;',\
                                        'padding: 0.75pt; border-bottom: 0.75pt dashed #999999; text-align: left;',\
                                        'padding: 0.75pt; border-bottom: 0.75pt dashed #999999; text-align: center;',\
                                        'border-right: 0.75pt dashed #999999; border-bottom: 0.75pt dashed #999999; text-align: center;']})
    
    entries_list = list(map(lambda element: element.getText().strip('\n').strip(u'\xa0'), table))
    #print(entries_list)
    rows_list = entries_list[5:]

    row = {}
    curr_time = get_irvine_time()
    for i in range(0, int(len(rows_list) / 4)):
        event_date = parse_date(rows_list[i*4])
        time = rows_list[i*4 + 3].split(' – ')
        end_time = normalize_time_from_str(time[1])
        if(curr_time.tm_year > event_date.tm_year or curr_time.tm_yday > event_date.tm_yday or normalize_time(curr_time) > end_time):
            continue
<<<<<<< Updated upstream
        row['date'] = get_date_str(event_date)
        row['name'] = rows_list[i*4 + 1]
        row['service_start'] = normalize_time_from_str(time[0])
        row['service_end'] = end_time
        break
=======
        event_list.append({
            'date': get_date_str(event_date),
            'name': rows_list[i+1],
            'service_start': normalize_time_from_str(start_time),
            'service_end': normalize_time_from_str(end_time)
        })
    if len(event_list) > 0:
        return event_list
    else:
        return  [
            {
                "date": "04/20/2069",
                "name": "placeholder",
                "service_start": 1100,
                "service_end": 2200
            }
        ]

>>>>>>> Stashed changes

    return row
