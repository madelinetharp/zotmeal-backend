from .CONSTANTS import LOCATION_INFO
import requests

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
    return requests.get(
            'https://uci.campusdish.com/api/menu/GetMenus?locationId={location_param}&periodId={meal_param}&date={date_param}'.format(
                location_param = get_id(location), 
                meal_param = meal_id, date_param = date)
            ).json()['Menu']

def get_schedule_data(location, date):
    '''
    Given a valid location and date,
    perform get request for the schedule_json
    '''
    return requests.get(
            'https://uci.campusdish.com/api/menu/GetMenuPeriods?locationId={location_param}&date={date_param}'.format(
                location_param = get_id(location), 
                date_param = date)
            ).json()['Result']
