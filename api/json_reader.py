from .CONSTANTS import MEAL_TO_PERIOD, PROPERTIES, DEFAULT_PRICES
from collections import defaultdict
import time

from .helpers import lower_first_letter, find_icon, normalize_time, \
        read_schedule_UTC, get_irvine_time, get_current_meal

from .location_management import is_valid_location, get_name, \
        get_id, get_menu_data, get_schedule_data

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
                'price' : DEFAULT_PRICES[lower_first_letter(meal['PeriodName'])],
            }
        ) for meal in schedule_json])

    return meal_periods

def get_diner_json(location: str, meal_id: int = None, date: str = None) -> dict:
    '''Given the name of a diner, get the corresponding JSON information and 
    return a Python dictionary of the relevant components'''

    if meal_id is None:
        meal_id = get_current_meal()

    if date is None:
        date = time.strftime('%m/%d/%Y')

    restaurant  = get_name(location)
    refreshTime = int(time.time())
    schedule    = extract_schedule(location, date)
    currentMeal = lower_first_letter(MEAL_TO_PERIOD[meal_id][1])
    foodItems   = []

    diner_json = {
        'restaurant'    : restaurant,
        'refreshTime'   : refreshTime,
        'schedule'      : schedule,
        'currentMeal'   : currentMeal,
        'all'           : foodItems,
    }

    menu_data = get_menu_data(location, meal_id, date)

    station_dict = extract_menu(
                    station_id_to_name  = dict([(entry['StationId'], entry['Name']) for entry in menu_data["MenuStations"]]),
                    products_list       = menu_data["MenuProducts"]
                    )
    
    for station_name in station_dict:
        diner_json['all'].append(
            {
                'station'   : station_name, 
                'menu'      : [{'category': category, 'items': items} for category, items in station_dict[station_name].items()]
            }
        )

    return diner_json
