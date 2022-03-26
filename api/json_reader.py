from .CONSTANTS import PROPERTIES, DEFAULT_PRICES
from collections import defaultdict
import time
from datetime import datetime, timezone, timedelta

from .helpers import lower_first_letter, find_icon, \
        read_schedule_UTC, get_current_meal, get_meal_name, get_irvine_date

from .location_management import get_name, \
        get_menu_data, get_schedule_data, get_event_data

from .sorting import station_ordering_key

def extract_menu(products_list, station_id_to_name):
    '''
    Given a list of all products and a dict translating station id to name
    return a dict...
    '''
    menu = defaultdict(lambda: defaultdict(lambda: []))

    for entry in products_list:
        details         = entry['Product']
        station_name    = station_id_to_name[entry['StationId']].replace('/ ',' / ')
        category_name   = details['Categories'][0]['DisplayName']

        item_dict = {
            'name'          : details['MarketingName'],
            'description'   : details['ShortDescription'],
            'nutrition'     : dict([(lower_first_letter(key), details[key]) for key in PROPERTIES]) | 
                {
                    'isEatWell'       : find_icon('EatWell', details),
                    'isPlantForward'  : find_icon('PlantForward', details),
                    'isWholeGrain'    : find_icon('WholeGrain', details),
                },
        } 

        menu[station_name][category_name].append(item_dict)
    return menu

def extract_schedule(location: str, date: str) -> dict:
    '''
    Given a location and a date as a string, perform a get request for that date's schedule,
    return a dict of the meal periods
    '''
    schedule_json = get_schedule_data(location, date)
    meal_periods = dict([
        (
            # this is the meal, e.g. 'breakfast', which will map to a dict of start/end time and price
            lower_first_letter(meal['PeriodName']), 
            {
                'start' : read_schedule_UTC(meal['UtcMealPeriodStartTime']),
                'end'   : read_schedule_UTC(meal['UtcMealPeriodEndTime']),
            }
        ) for meal in schedule_json])

    return meal_periods

def get_diner_json(location: str, meal_id: int = None, date: str = None) -> dict:
    '''Given the name of a diner, get the corresponding JSON information and 
    return a Python dictionary of the relevant components'''

    if meal_id is None:
        meal_id = get_current_meal()

    if date is None:
        #from imports at top of file: from datetime import datetime, timezone, timedelta
        date = get_irvine_date()#current date in Irvine

    meal_calc   = meal_id
    restaurant  = get_name(location)
    refreshTime = int(time.time())
    schedule    = extract_schedule(location, date)
    currentMeal = get_meal_name(schedule, meal_id)

    diner_json = {
        'meal'          : meal_calc,
        'date'          : date,
        'restaurant'    : restaurant,
        'refreshTime'   : refreshTime,
        'schedule'      : schedule,
        'currentMeal'   : currentMeal,
        'price'         : DEFAULT_PRICES,
        'all'           : [],
        'themed'        : get_event_data(restaurant)
    }
    print(f'serving request using meal_id {meal_id} and date {date}')
    menu_data = get_menu_data(location, meal_id, date)

    station_dict = extract_menu(
                    station_id_to_name  = dict([(entry['StationId'], entry['Name']) for entry in menu_data["MenuStations"]]),
                    products_list       = menu_data["MenuProducts"]
                    )
    
    for station_name in sorted(station_dict, key=station_ordering_key):#iterate over station names in custom order
        diner_json['all'].append(
            {
                'station'   : station_name, 
                'menu'      : [{'category': category, 'items': items} for category, items in station_dict[station_name].items()]
            }
        )

    return diner_json
