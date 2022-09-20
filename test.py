import json
from api.campusdish_interface import get_menu_data

with open("eaterytest.json", "w") as f:
    json.dump(get_menu_data("anteatery"),f)