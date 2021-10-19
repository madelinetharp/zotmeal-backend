from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
from bs4 import BeautifulSoup#imported to parse site contents into dicts
import json#imported to format dict as json string
import urllib.parse, urllib.request #imported to get site contents from internet
import time#imported to get timestamp
import traceback#for error handling
import os

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
        if meal == None:
            meal = get_current_meal()
        if date == None:
            date = time.strftime("%m/%d/%Y")
        modified_datestring = date.replace("/","|")
        return db.reference(f"{location}/{modified_datestring}/{meal}")
        #for the returned reference, get() returns None when there's nothing created at that path.

def get_irvine_time() -> tuple:#tuple of two ints for hours and minutes
    seconds_since_epoch = int(time.time())#epoch is at 0:00 UTC
    hours_since_epoch = seconds_since_epoch/3600
    uci_hour = (hours_since_epoch-7+24)%24#uci time is UTC-7, and the +24 is to avoid negative numbers
    uci_minute = (uci_hour%1)*60
    return (int(uci_hour),int(uci_minute))

def get_current_meal():
    hour, minute = get_irvine_time()
    if hour<11:
        return 0
    elif hour<17 or hour==16 and minute<30:
        return 1
    else:
        return 2
brandy_info = ("Brandywine","https://uci.campusdish.com/LocationsAndMenus/Brandywine",3314)
eatery_info = ("Anteatery","https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery",3056)

url_dict = {
    "Brandywine":brandy_info,
    "brandywine":brandy_info,
    "TheAnteatery":eatery_info,
    "Anteatery":eatery_info,
    "anteatery":eatery_info
}

def scrape_menu_to_dict(location: str, meal: int = None, date: str = None) -> dict:
    restaurant, url, id = url_dict[location]

    if meal==None:
        query=""
    else:
        if date==None:
            date = time.strftime("%m/%d/%Y")#urllib quote URL-encodes the slashes
        query = f"?locationId={id}&storeIds=&mode=Daily&periodId={105+meal}&date={urllib.parse.quote(date)}"
    entire_body = BeautifulSoup(urllib.request.urlopen(url+query).read(), 'html.parser')
    stations = entire_body.find_all("div",{"class": "menu__station"})
    
    complete_dict = dict()
    complete_dict["refreshTime"] = int(time.time())#unix epoch time
    complete_dict["restaurant"] = restaurant#restaurant name is either brandywine or anteatery
    complete_dict["all"] = []#contains list of all stations
    for station_node in stations:
        station_dict = dict()
        station_dict['station'] = station_node.find("div", {"class": "station-header-title"}).string
        station_dict['menu'] = []
        categories = station_node.find_all("div",{"class": "menu__parentCategory"})
        for category_node in categories:
            category_dict = dict()
            category_dict["category"] = category_node.find("span",{"class":"categoryName"}).string
            category_dict["items"] = []
            items = category_node.find_all("li", {"class": "menu__item item"})
            for item_node in items:
                item_dict = dict()
                menu_name = item_node.find("a", {"class": "viewItem"})
                calories = item_node.find("span", {"class": "item__calories"})
                description = item_node.find("p", {"class": "item__content"})
                vegan = item_node['isvegan']
                vegetarian = item_node['isvegetarian']
                img_container = item_node.find("ul", {"class": "unstyled item__allergens allergenList"})

                item_dict["name"] = menu_name.string if menu_name else item_node.find("span", {"class": "item__name"}).string

                item_dict["calories"] = int(calories.string.split()[0]) if calories else 0

                item_dict["description"] = description.string or 'N/A' if description else 'N/A'

                item_dict["isVegan"] = vegan=="True"

                item_dict["isVegetarian"] = vegetarian=="True"

                item_dict["isEatWell"] = False
                item_dict["isPlantForward"] = False
                item_dict["isWholeGrains"] = False
                
                if img_container!= None:
                    for img_node in img_container.find_all("img"):
                        if img_node["src"] == "/-/media/Global/All Divisions/Dietary Information/EatWell-80x80.png":
                            item_dict["isEatWell"] = True
                        elif img_node["src"] == "/-/media/Global/All Divisions/Dietary Information/PlantForward.png":
                            item_dict["isPlantForward"] = True
                        elif img_node["src"] == "/-/media/Global/All Divisions/Dietary Information/WholeGrains-80x80.png":
                            item_dict["isWholeGrains"] = True

                category_dict["items"].append(item_dict)
            station_dict["menu"].append(category_dict)
        complete_dict["all"].append(station_dict)
    return complete_dict

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
            self.wfile.write(json.dumps(data,ensure_ascii=False).encode())
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


