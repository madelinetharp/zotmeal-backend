import json
import time
from collections import defaultdict
import requests


brandy_info = ('Brandywine', 'https://uci.campusdish.com/api/menu/GetMenus?locationId=3314&periodId={meal_param}&date={date_param}'.format)
eatery_info = ('Anteatery', 'https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&periodId={meal_param}&date={date_param}'.format)

brandy_info = ('Brandywine', 'https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&date=01/19/2022'.format)

ALL_LOCATIONS = {
    "brandywine"    : brandy_info,
    "anteatery"     : eatery_info
}

MEAL_ID = {
    0: 49,
    1: 106,
    2: 107,
    3: 2651
}

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
    "SaturatedFat",
)


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
    return s[0].lower() + s[1:]


def request_location(url: str) -> dict:
    pass


def scrape_menu_to_dict(location: str, meal_id: int = None, date: str = None) -> dict:
    '''Given a location of a cafeteria, get the corresponding JSON information and 
    return a Python dictionary of the relevant components'''
    
    restaurant, url = ALL_LOCATIONS[location]

    if meal_id is None:
        meal_id = get_current_meal()

    if date is None:
        date = time.strftime("%m/%d/%Y")

    url = url(meal_param = MEAL_ID[meal_id], date_param = date)
    data = requests.get(url).json()

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
