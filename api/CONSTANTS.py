#anteatery 01/14/2022 breakfast
#https://uci.campusdish.com/api/menu/GetMenus?locationId=3056&date=01/14/2022&periodId=49

# brandywine lunch 10/14/2021: https://uci.campusdish.com/en/LocationsAndMenus/Brandywine?locationId=3314&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
# anteatery examples:
# example url with query (10/14/2021 lunch): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=106&date=10%2F14%2F2021
# example 2 (10/14/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F14%2F2021
# (10/15/2021 dinner): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=107&date=10%2F15%2F2021
# (10/21/2021 breakfast): https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery?locationId=3056&storeIds=&mode=Daily&periodId=105&date=10%2F21%2F2021

# request URLS bound to the .format method
MENU_REQUEST      = 'https://uci.campusdish.com/api/menu/GetMenus?locationId={location_param}&meal={meal_param}&date={date_param}'.format
SCHEDULE_REQUEST  = 'https://uci.campusdish.com/api/menu/GetMenuPeriods?locationId={location_param}&date={date_param}'.format

LOCATION_INFO = {
    'brandywine': {
        'official'  : 'Brandywine',
        'id'        : 3314,
    },

    'anteatery': {
        'official'  : 'Anteatery',
        'id'        : 3056,
    }
}

DEFAULT_PRICES = {
    'breakfast' : 9.75,
    'lunch'     : 13.75,
    'brunch'    : 13.75,
    'dinner'    : 14.95
}

# Default opening and closing times
# TODO: Might implement a class to determine default open/close depending on day
DEFAULT_OPEN    = 715
DEFAULT_CLOSE   = 2200


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
    0: (49, 'breakfast'),
    1: (106, 'lunch'),
    2: (107, 'dinner'),
    3: (2651, 'brunch')
}

