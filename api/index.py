from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
import json#imported to format dict as json string
import urllib.parse, urllib.request #imported to get site contents from internet
import time#imported to get timestamp
import traceback#for error handling
import os
from datetime import datetime
from collections import defaultdict
import requests 
#anteatery 01/14/2022 breakfast
#https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&date=01/14/2022&periodId=49

brandy_info = ('Brandywine', 'https://uci.campusdish.com/api/menu/GetMenus?locationId=3314&periodId={meal_param}&date={date_param}'.format)
eatery_info = ('Anteatery', 'https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&periodId={meal_param}&date={date_param}'.format)

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


ALL_LOCATIONS = {
    'brandywine'    : brandy_info,
    'anteatery'     : eatery_info
}

MEAL_IDS = {
    0: 49,
    1: 106,
    2: 107,
    3: 2651
}

USE_CACHE = bool(os.getenv("USE_CACHE"))

print("Using cache" if USE_CACHE else "Not using cache")

if USE_CACHE:
    #ideally this firebase stuff would be in a separate file but idk how to get vercel to let me import my own files into eachother
    import firebase_admin#https://firebase.google.com/docs/database/admin/start
    from firebase_admin import credentials
    from firebase_admin import db
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_ADMIN_CREDENTIALS")))

    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
    })


    def get_db_reference(location: str, meal: int, date: str) -> firebase_admin.db.Reference:
        if meal is None:
            meal = get_current_meal()

        if date is None:
            date = time.strftime("%m/%d/%Y")

        modified_datestring = date.replace("/","|")
        
        # .get() returns None if nothing created
        return db.reference(f"{location}/{modified_datestring}/{meal}")


def get_current_meal():
    '''Return meal code for current time of the day'''
    local_time = time.gmtime(time.time() - 28800)
    now = int(f'{local_time.tm_hour}{local_time.tm_min}')
    
    breakfast   = 0000
    lunch       = 1100
    dinner      = 1630
    
    # After 16:30, Dinner, Meal-Code: 2
    if now >= dinner:
        return 2

    # After 11:00 Weekend, Brunch, Meal-Code: 3
    if now >= lunch and local_time.tm_wday >= 5:
        return 3

    # After 11:00 Weekday, Lunch, Meal-Code: 1
    if now >= lunch:
        return 1

    # After 00:00, Breakfast, Meal-Code: 0
    if now >= breakfast:
        return 0


def uncapitalize_first_letter(s: str) -> str:
    'Capitalize the first letter of a string'
    return s[0].lower() + s[1:]


def scrape_menu_to_dict(location: str, meal_id: int = None, date: str = None) -> dict:
    '''Given a location of a cafeteria, get the corresponding JSON information and 
    return a Python dictionary of the relevant components'''
    
    restaurant, unformatted_url = ALL_LOCATIONS[location]

    if meal_id is None:
        meal_id = get_current_meal()

    if date is None:
        date = time.strftime("%m/%d/%Y")#urllib quote URL-encodes the slashes

    data = requests.get(
            unformatted_url(meal_param = MEAL_IDS[meal_id], date_param = date)
            ).json()

    menu_data = data["Menu"]
    
    final_dict = {
        'refreshTime'   : int(time.time()),
        'restaurant'    : restaurant,
        'all'           : [],
    }

    station_dict        = defaultdict(lambda: defaultdict(lambda: []))

    stations_list       = menu_data["MenuStations"]
    station_id_to_name  = dict([(entry['StationId'], entry['Name']) for entry in stations_list])
    products_list       = menu_data["MenuProducts"]


    def _find_icon(icon_property, food_info):
        return any(map(lambda diet_info: icon_property in diet_info["IconUrl"], food_info["DietaryInformation"]))

    for entry in products_list:
        details = entry["Product"]
        station_name = station_id_to_name[entry["StationId"]].replace("/ "," / ")
        category_name = details["Categories"][0]["DisplayName"]

        item_dict = {
            'name'          : details['MarketingName'],
            'description'   : details['ShortDescription'],
            'nutrition'     : dict([(uncapitalize_first_letter(key), details[key]) for key in PROPERTIES]) | 
                {
                'isEatWell'       : _find_icon('EatWell', details),
                'isPlantForward'  : _find_icon('PlantForward', details),
                'isWholeGrain'    : _find_icon('WholeGrain', details),
                },
        } 

        station_dict[station_name][category_name].append(item_dict)
    
    for station_name in station_dict.keys():

        final_dict["all"].append({
        'station'   : station_name, 
        'menu'      : [{'category': category, 'items': items} for category, items in station_dict[station_name].items()]
        })

    return final_dict

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

        if location not in ALL_LOCATIONS.keys():
            raise InvalidQueryException(f'The location specified is not valid. Valid locations: {list(ALL_LOCATIONS.keys())}')

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
                    data = scrape_menu_to_dict(location, meal, date)
                    db_ref.set(data)

                else:
                    data = db_data
            else:
                data = scrape_menu_to_dict(location, meal, date)
                    
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
                    data        = 'Internal Server Error. Raise an issue on the github repo: https://github.com/EricPedley/zotmeal-backend'
            )

