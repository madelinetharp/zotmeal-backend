from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
from bs4 import BeautifulSoup#imported to parse site contents into dicts
import json#imported to format dict as json string
import urllib.request #imported to get site contents from internet

def scrape_menu_to_str(url,name):
    entire_body = BeautifulSoup(urllib.request.urlopen(url).read(), 'html.parser')
    stations = entire_body.find_all("div",{"class": "menu__station"})
    
    complete_dict = dict()
    complete_dict[name] = []#name is either brandywine or anteatery
    for station_node in stations:
        station_dict = dict()
        station_dict['station'] = station_node.find("div", {"class": "station-header-title"}).string
        station_dict['menu'] = []
        categories = entire_body.find_all("div",{"class": "menu__parentCategory"})
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
                eatwell = item_node.find("ul", {"class": "unstyled item__allergens allergenList"})

                item_dict["name"] = menu_name.string if menu_name else item_node.find("span", {"class": "item__name"}).string

                item_dict["calories"] = int(calories.string.split()[0]) if calories else 0

                item_dict["description"] = description.string or 'N/A' if description else 'N/A'

                item_dict["isVegan"] = bool(vegan)

                item_dict["isVegetarian"] = bool(vegetarian)

                item_dict["isEatWell"] = False
                if eatwell!= None:
                    for x in eatwell.find_all("img"):
                        #print(x)
                        if x["src"] == "/-/media/Global/All Divisions/Dietary Information/EatWell-80x80.png":
                            item_dict["isEatWell"] = True

                item_dict["isPlantForward"] = False
                if eatwell!= None:
                    for x in eatwell.find_all("img"):
                        if x["src"] == "/-/media/Global/All Divisions/Dietary Information/PlantForward.png":
                            item_dict["isPlantForward"] = True

                item_dict["isWholeGrains"] = False
                if eatwell != None:
                    for x in eatwell.find_all("img"):
                        if x["src"] == "/-/media/Global/All Divisions/Dietary Information/WholeGrains-80x80.png":
                            item_dict["isWholeGrains"] = True


                category_dict["items"].append(item_dict)
            station_dict["menu"].append(category_dict)

        complete_dict[name].append(station_dict)
    return json.dumps(complete_dict)

eatery_url = "https://uci.campusdish.com/en/LocationsAndMenus/TheAnteatery"
brandy_url = "https://uci.campusdish.com/LocationsAndMenus/Brandywine"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = ""
        if "anteatery" in self.path:
            data = scrape_menu_to_str(eatery_url)
        elif "brandywine" in self.path:
            data = scrape_menu_to_str(brandy_url)
        else:
            self.send_response(404)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Invalid path. Needs to be /anteatery or /brandywine".encode())
            return
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        self.wfile.write(data.encode())
        return


