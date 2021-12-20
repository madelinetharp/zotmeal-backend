from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
import json#imported to format dict as json string
import urllib.parse, urllib.request #imported to get site contents from internet
import time#imported to get timestamp
import traceback#for error handling
import os#imported to get environment variables
from collections import defaultdict
import requests 
from .helpers import *

#anteatery 01/14/2022 breakfast
#https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&date=01/14/2022&periodId=49


# Class to store general information, queries, and perform operations on them
class LocationManager:
    MENU_QUERY      = 'https://uci.campusdish.com/api/menu/GetMenus?locationId={location_param}&periodId={meal_param}&date={date_param}'.format
    SCHEDULE_QUERY  = 'https://uci.campusdish.com/api/menu/GetMenuPeriods?locationId={location_param}&date={date_param}'.format 

    LOCATION_INFO   = {
        'brandywine': {
            'official'  : 'Brandywine',
            'id'        : 3314,
        },

        'anteatery': {
            'official'  : 'Anteatery',
            'id'        : 3056,
        }
    }

    def __init__(self):
        pass

    # TODO: make location validater and resolver more robust/accurate; maybe create a __check_alias upon not-immediate match
    def is_valid_location(self, location: str) -> bool:
        'Check if the location is valid'
        if location in self.LOCATION_INFO:
            return True
        return False

    def resolve_location(self, location: str) -> bool:
        '''
        Assuming the location is a valid alias,
        resolve the location to a key in the ALL_LOCATIONS dict
        '''
        return location.lower()

    def get_name(self, location: str):
        'Assuming valid location is provided, return the official name for diner'
        return self.LOCATION_INFO[location]['official']

    def get_id(self, location: str) -> int:
        'Assuming valid location is provided, return id for diner'
        return self.LOCATION_INFO[location]['id']
    
    def get_menu_data(self, location, meal_id, date):
        '''
        Given a valid location, meal_id, and date,
        perform get request for the diner_json and return the dict at diner_json['Menu']
        '''
        return requests.get(
                self.MENU_QUERY(location_param = self.get_id(location), meal_param = meal_id, date_param = date)
                ).json()['Menu']
    
    def get_schedule_json(self, location, date):
        '''
        Given a valid location and date,
        perform get request for the schedule_json
        '''
        return requests.get(
                self.SCHEDULE_QUERY(location_param = self.get_id(location), date_param = date)
                ).json()['Result']


# Initialize a location manager
GLOBAL_LOCATION_MANAGER = LocationManager()

# Default opening and closing times
# TODO: Might implement a class to determine default open/close depending on day
DEFAULT_OPEN    = 715
DEFAULT_CLOSE   = 2200

# Default offset for Irvine from GMT (GMT-8 = -28000 seconds)
IRVINE_OFFSET = -28800

# Relevant Nutrition Properties
PROPERTIES = (
    'IsVegan',
    'IsVegetarian',
    'ServingSize',
    'ServingUnit',
    'Calories',
    'CaloriesFromFat',
    'TotalFat',
    'TransFat',
    'Cholesterol',
    'Sodium',
    'TotalCarbohydrates',
    'DietaryFiber',
    'Sugars',
    'Protein',
    'VitaminA',
    'VitaminC',
    'Calcium',
    'Iron',
    'SaturatedFat'
)

# MEAL ID > (PERIOD ID, MEAL NAME)
# meals can be referred to by their id or period id alias
# TODO: there might be a better way to implement this
MEAL_TO_PERIOD = {
    0: (49, 'Breakfast'),
    1: (106, 'Lunch'),
    2: (107, 'Dinner'),
    3: (2651, 'Brunch')
}

USE_CACHE = bool(os.getenv("USE_CACHE"))

print("Using cache" if USE_CACHE else "Not using cache")

# TODO: need to clear Firebase cache of outdated JSONS, should probably implement timer
# e.g. force refresh of cache every hour
USE_CACHE = False

if USE_CACHE:
    #ideally this firebase stuff would be in a separate file but idk how to get vercel to let me import my own files into eachother
    import firebase_admin#https://firebase.google.com/docs/database/admin/start
    from firebase_admin import credentials
    from firebase_admin import db
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_ADMIN_CREDENTIALS")))

    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
    })

    def get_db_reference(location: str, meal: int, date: str) -> db.Reference:
        if meal is None:
            meal = get_current_meal()

        if date is None:
            irvine_time = get_irvine_time()
            date = f"{irvine_time.tm_mon}/{irvine_time.tm_mday}/{irvine_time.tm_year}"

        modified_datestring = date.replace("/","|")
        
        # .get() returns None if nothing created
        return db.reference(f"{location}/{modified_datestring}/{meal}")




# Basic Operations
def get_irvine_time():
    'Return the local time in normalized format'
    local_time = time.gmtime(time.time() + IRVINE_OFFSET)
    return local_time

def check_open(breakfast_start: int = DEFAULT_OPEN, dinner_end: int = DEFAULT_CLOSE, time=None):
    'Given the start time for breakfast and end time for dinner, return true if the diner is open'
    if time is None:
        time = get_irvine_time()
    return time in range(breakfast_start, dinner_end)

def get_current_meal():
    '''
    Return meal code for current time of the day
    Note: it does not consider open/closing; Breakfast begins at 12:00AM, and Dinner ends at 12:00AM
    '''
    irvine_time = get_irvine_time()
    now = _normalize_time(irvine_time)

    breakfast   = 0000
    lunch       = 1100
    dinner      = 1630
    
    # After 16:30, Dinner, Meal-Code: 2
    if now >= dinner:
        return 2

    # After 11:00 Weekend, Brunch, Meal-Code: 3
    if now >= lunch and irvine_time.tm_wday >= 5:
        return 3

    # After 11:00 Weekday, Lunch, Meal-Code: 1
    if now >= lunch:
        return 1

    # After 00:00, Breakfast, Meal-Code: 0
    if now >= breakfast:
        return 0


# JSON parsing functions
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
            'nutrition'     : dict([(_lower_first_letter(key), details[key]) for key in PROPERTIES]) | 
                {
                    'isEatWell'       : _find_icon('EatWell', details),
                    'isPlantForward'  : _find_icon('PlantForward', details),
                    'isWholeGrain'    : _find_icon('WholeGrain', details),
                },
        } 

        menu[station_name][category_name].append(item_dict)
    return menu

def extract_schedule(location: str, date: str) -> dict:
    '''
    Given a location and a date as a string, perform a get request for that date's schedule,
    return a dict of the meal periods
    '''
    schedule_json = GLOBAL_LOCATION_MANAGER.get_schedule_json(location, date)
    meal_periods = dict([
        (
            _lower_first_letter(meal['PeriodName']), 
            {
                'start' : _read_schedule_UTC(meal['UtcMealPeriodStartTime']),
                'end'   : _read_schedule_UTC(meal['UtcMealPeriodEndTime']),
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

    restaurant  = GLOBAL_LOCATION_MANAGER.get_name(location)
    refreshTime = int(time.time())
    schedule    = extract_schedule(location, date)
    currentMeal = _lower_first_letter(MEAL_TO_PERIOD[meal_id][1])
    foodItems   = []

    diner_json = {
        'restaurant'    : restaurant,
        'refreshTime'   : refreshTime,
        'schedule'      : schedule,
        'currentMeal'   : currentMeal,
        'all'           : foodItems,
    }

    menu_data = GLOBAL_LOCATION_MANAGER.get_menu_data(location, meal_id, date)

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

# brandywine lunch 10/14/2021: https://uci.campusdish.com/en/LocationsAndMenus/Brandywine?locationId=3314&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
# anteatery examples:
# example url with query (10/14/2021 lunch): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
# example 2 (10/14/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F14%2F2021
# (10/15/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F15%2F2021
# (10/21/2021 breakfast): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=105&date=10%2F21%2F2021

class InvalidQueryException(Exception):
    pass

class NotFoundException(Exception):
    pass

# to implement redirects see this: https://stackoverflow.com/questions/22701544/redirect-function-with-basehttprequesthandler
# redirects could be useful to just send the request straight to firebase

class handler(BaseHTTPRequestHandler):

    def process_response(self, status_code: int, headers: tuple, data) -> None:
        ''' 
        Given a status_code, headers, and data, forward the information to the client
        '''

        self.send_response(status_code)
        self.send_header(*headers)
        self.end_headers()
        self.wfile.write(data.encode())

    def __read_get(self) -> ('path', 'params', 'query'):
        '''
        If a get request is made, validate the path, params, and raw query
        valid   : return the 3 relevant values in a tuple
        invalid : raise NotFoundException
        '''
        _, _, path, params, raw_query, _ = urllib.parse.urlparse("//"+self.path)#prepending the // separates netloc and path

        if not path == "/api" or path == "/api/":
            raise NotFoundException

        query = urllib.parse.parse_qs(raw_query)

        return path, params, query


    def __validate_query_location(self, query) -> 'location':
        '''
        Given a query, verify that a location is present and valid
        valid   : return the location in lowercase
        invalid : raise InvalidQueryException
        '''

        if 'location' not in query:
            raise InvalidQueryException('No location query parameter specified')
        
        location = query['location'][0]

        if not GLOBAL_LOCATION_MANAGER.is_valid_location(location):
            raise InvalidQueryException(f'The location specified is not valid. Valid locations: {list(LocationManager.LOCATION_INFO.keys())}')

        return location

    def __validate_query_meal_date(self, query) -> ('meal', 'date'):
        '''
        Given a query, check if there is a valid combination of meal_id and date
        valid   : return the two values in a tuple
        invalid : raise InvalidQueryException
        '''

        if 'meal' in query:
            meal = int(query['meal'][0])

        else:
            meal = None

        if 'date' in query:
            date = query['date'][0] # note: data gets decoded by urllib, so it will contain slashes.

        else:
            date = None

        if meal is None and not date is None:
            raise InvalidQueryException('You can\'t provide the date without the meal (not implemented in the server).')

        return meal, date

    def do_GET(self):
        '''
        Given a get request for food, respond accordingly
        '''

        try:
            path, params, query = self.__read_get()
            location            = self.__validate_query_location(query)
            meal, date          = self.__validate_query_meal_date(query)

            if USE_CACHE:
                print(f'date from query params: {date}')
                db_ref = get_db_reference(location, meal, date)

                db_data = db_ref.get()

                if(db_data is None):
                    data = get_diner_json(location, meal, date)
                    db_ref.set(data)

                else:
                    data = db_data
            else:
                data = get_diner_json(location, meal, date)
                    
            self.process_response(
                    status_code = 200, 
                    headers     = ('Content-type', 'application/json'), 
                    data        = json.dumps(data, ensure_ascii = False, indent = 4)
            )

        except NotFoundException:
            self.process_response(
                    status_code = 404, 
                    headers     = ('Content-type', 'text/plain'), 
                    data        = 'Invalid path. The only one available is /api'
            )

        except InvalidQueryException as e:
            self.process_response(
                status_code = 400, 
                headers     = ('Content-type', 'text/plain'), 
                data        = f'Invalid query parameters. Details: {e}'
        )
            
        except Exception as e:
            traceback.print_exc()
            self.process_response(
                    status_code = 500, 
                    headers     = ('Content-type', 'text/plain'), 
                    data        = f'Internal Server Error. Raise an issue on the github repo: https://github.com/EricPedley/zotmeal-backend. Details: {e}'
            )

