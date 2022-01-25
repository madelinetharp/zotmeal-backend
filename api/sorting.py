ORDERINGS = [
    'Home',# anteatery main dish
    'Oven',# anteatery pizza
    'Grubb / Mainline',# brandywine main dish
    'Compass',# brandywine main dish 2
    'Hearth/Pizza',# brandywine pizza
    'Sizzle Grill',# anteatery burgers
    'Ember/Grill',# brandywine burgers
    'Vegan',# both vegan
    'Bakery',# anteatery dessert
    'Soups',# both soup
    "Farmer's Market",# anteatery salad
    'The Farm Stand / Salad Bar'# brandywine salad
]

def station_ordering_key(station_name: str) -> int:
    '''
    Returns an integer used to sort station names by relevance (basically Eric's personal preferences :) )
    '''
    try:
        return ORDERINGS.index(station_name)
    except ValueError:# if 
        print(f"ValueError on station orderings. Key {station_name} is not in list")
        return len(ORDERINGS)