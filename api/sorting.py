ORDERINGS = [
    'Home',# anteatery main dish
    'Oven',# anteatery pizza
    'Grubb / Mainline',# brandywine main dish
    'Compass',# brandywine main dish 2
    'Hearth/Pizza',# brandywine pizza
    'Bakery',# anteatery dessert
    'Sizzle Grill',# anteatery burgers
    'Ember/Grill',# brandywine burgers
    'Soups',# both soup
    'Vegan',# both vegan
    "Farmer's Market",# anteatery salad
    'The Farm Stand / Salad Bar'# brandywine salad
]

def station_ordering_key(station_name: str) -> int:
    '''
    Returns a function used to sort stations in the preferred order. See sorting.py -> ORDERINGS to know in what order they're sorted in.
    '''
    try:
        return ORDERINGS.index(station_name)
    except ValueError:# if 
        print(f"ValueError on station orderings. Key {station_name} is not in list")
        return len(ORDERINGS)