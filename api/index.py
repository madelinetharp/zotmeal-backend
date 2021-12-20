from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
import json#imported to format dict as json string
import urllib.parse, urllib.request #imported to get site contents from internet
import time#imported to get timestamp
import traceback#for error handling
import os
from datetime import datetime
from collections import defaultdict
#anteatery 01/14/2022 breakfast
#https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&date=01/14/2022&periodId=49

brandy_info = ("Brandywine", "https://uci.campusdish.com/api/menu/GetMenus?locationId=3314")
eatery_info = ("Anteatery", "https://uci.campusdish.com/api/menu/GetMenus?locationId=3056")

PROPERTIES = (
    "IsVegan",
    "IsVegetarian",
    "ServingSize",
    "ServingUnit",
    "Calories",
    "CaloriesFromFat",
    "TotalFat",
    "TransFat",
    "Cholesterol",
    "Sodium",
    "TotalCarbohydrates",
    "DietaryFiber",
    "Sugars",
    "Protein",
    "VitaminA",
    "VitaminC",
    "Calcium",
    "Iron",
    "SaturatedFat"
)


ALL_LOCATIONS = {
    "Brandywine"    : brandy_info,
    "brandywine"    : brandy_info,
    "TheAnteatery"  : eatery_info,
    "Anteatery"     : eatery_info,
    "anteatery"     : eatery_info
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
        return db.reference(f"{location}/{modified_datestring}/{meal}")
        #for the returned reference, get() returns None when there's nothing created at that path.

def get_irvine_time() -> tuple:#tuple of two ints for hours and minutes
    '''Return current time in Irvine, PST, by subtracing 8 hours (in seconds) from GMT'''
    local_time = time.gmtime(time.time() - 28800)
    return local_time.tm_hour, local_time.tm_min

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
    return s[0].lower()+s[1:]

def scrape_menu_to_dict(location: str, meal_id: int = None, date: str = None) -> dict:
    '''Given a location of a cafeteria, get the corresponding JSON information and 
    return a Python dictionary of the relevant components'''
    
    restaurant, url = ALL_LOCATIONS[location]

    if meal_id is None:
        meal_id = get_current_meal()

    if date is None:
        date = time.strftime("%m/%d/%Y")#urllib quote URL-encodes the slashes

    url += f"&periodId={MEAL_IDS[meal_id]}&date={date}"
    r = urllib.request.urlopen(url)
    data = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    menu_data = data["Menu"]
    
    final_dict = {
        'refreshTime'   : int(time.time()),
        'restaurant'    : restaurant,
        'all'           : [],
    }

    intermediate_dict = defaultdict(lambda: defaultdict(lambda: []))

    stations_list = menu_data["MenuStations"]
    station_id_to_name = dict([(entry['StationId'], entry['Name']) for entry in stations_list])

    products_list = menu_data["MenuProducts"]


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

        intermediate_dict[station_name][category_name].append(item_dict)
    
    for station_name in intermediate_dict.keys():

        final_dict["all"].append({
        'station'   : station_name, 
        'menu'      : [{'category': category, 'items': items} for category, items in intermediate_dict[station_name].items()]
        })

    return final_dict

#brandywine lunch 10/14/2021: https://uci.campusdish.com/en/LocationsAndMenus/Brandywine?locationId=3314&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
#anteatery examples:
#example url with query (10/14/2021 lunch): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
#example 2 (10/14/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F14%2F2021
# (10/15/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F15%2F2021
# (10/21/2021 breakfast): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=105&date=10%2F21%2F2021

class InvalidQueryException(Exception):
    pass
class NotFoundException(Exception):
    pass

#to implement redirects see this: https://stackoverflow.com/questions/22701544/redirect-function-with-basehttprequesthandler
#redirects could be useful to just send the request straight to firebase
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            scheme, netloc, path, params, query, fragment = urllib.parse.urlparse("//"+self.path)#prepending the // separates netloc and path
            if not path == "/api" or path == "/api/":
                raise NotFoundException

            query_params = urllib.parse.parse_qs(query)

            try:
                query_keys = query_params.keys()
                if not "location" in query_keys:
                    raise InvalidQueryException("No location query parameter specified")
                location = query_params["location"][0]
                if not location in url_dict.keys():#url_dict is in global scope
                    raise InvalidQueryException(f"The location specified is not valid. Valid locations: {list(url_dict.keys())}")
                meal=None
                date=None
                if "meal" in query_keys:
                    meal = int(query_params["meal"][0])
                    if "date" in query_keys:
                        date = query_params["date"][0]#note: data gets decoded by urllib, so it will contain slashes.
                elif "date" in query_keys:
                    raise InvalidQueryException("You can't provide the date without the meal (not implemented in the server). LMK if you think there is a use for providing only the date.")
                if USE_CACHE:
                    print(f"date from query params: {date}")
                    db_ref = get_db_reference(location, meal, date)
                    db_data = db_ref.get()
                    if(db_data==None):
                        data = scrape_menu_to_dict(location, meal, date)
                        db_ref.set(data)
                    else:
                        data = db_data
                else:
                    data = scrape_menu_to_dict(location, meal, date)
                
            except InvalidQueryException as e:
                self.send_response(400)
                self.send_header('Content-type','text/plain')
                self.end_headers()
                self.wfile.write(f"Invalid query parameters. Details: {e}".encode())
                return
            
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            #json.dump(data,self.wfile,ensure_ascii=False) #TODO: this clean solution doesn't work for some reason. says bytes-like is required, not str. figure out why
            self.wfile.write(json.dumps(data,ensure_ascii=False, indent = 4).encode())

        except NotFoundException:
            self.send_response(404)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Invalid path. The only one available is /api".encode())

        except Exception as e:
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Internal Server Error. Raise an issue on the github repo: https://github.com/EricPedley/zotmeal-backend".encode())


