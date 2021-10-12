from typing import List, Tuple, Iterable, NamedTuple
import re
import urllib.request
#typing annotations for python 3.8 and below
#https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html

'''
    Returns a list of bool, presences, where presences[i] denotes whether or not keywords[i] is present in test_string
    i.e presences[i] = keywords[i] in test_string
'''
def findMultiple(test_string: str, keywords: List[str]) -> List[bool]:#list[str] doesn't need quotes on python >=3.9
    presences = [False]*len(keywords)
    traversal_list = [[i,keywords[i]] for i in range(len(keywords))]
    for char in test_string:
        for index, position_keyword_pair in enumerate(traversal_list):
            #position_keyword_pair is a List[int,str]
            #python sucks because I can't unpack position_keyword_pair[0] as an integer reference without cheesy shit like wrapping it in a list
            if presences[index]:
                continue
            if char==position_keyword_pair[1][position_keyword_pair[0]]:
                position_keyword_pair[0]+=1
            else:
                position_keyword_pair[0]=0
            if position_keyword_pair[0]==len(position_keyword_pair[1]):
                presences[index] = True
    return presences

# print(findMultiple("this string contains many words",["string","contains","bannaa","container"]))

def getWebsiteBody(url: str) -> str:#returns the html content returned by a GET request to the specified URL
    return bytes.decode(urllib.request.urlopen(url).read())
def parseForStations(body: str) -> List[Tuple[str,str]]:#takes the html body of the dining website and returns a list of tuples, each containing the station's name and the html content for that station
    #regex for each station: r"station-header-title.*?>(.*?)<.*?<\/div>\s+<\/div>\s+</div>"
    # full match: everything about the menu station (including items). Run second regex on this string for each station.
    # group 1: the name of the menu station
    return re.findall(r"station-header-title.*?>(.*?)<(.*?)<\/div>\s+<\/div>\s+</div>",body,re.S)

#using namedtuples because they're like structs, and MenuItem doesn't need methods
MenuItem = NamedTuple("MenuItem",[("name",str),("calories",int),("description",str),("categories",List[bool])])

def parseForItems(reduced_body: str) -> Iterable[MenuItem]:#takes the html body of each station and returns a list of the menu items in that station
    #regex for each item within a station: r"menu__item.*?#\">(.*?)<.*?__calories\">(.*?) Calories.*?__content\">(.*?)<(.*?)<\/ul>"
    # full match: everything about the item
    # group 1: name of item
    # group 2: calories of item
    # group 3: description of item
    # group 4: remaining info, which includes categories like EatWell or Vegan. Run a find for EatWell, Vegan, Vegetarian, etc. for this one.
    raw = re.findall(r"#\">(.*?)<.*?__calories\">(.*?)<.*?\">(.*?)<(.*?)product-divider",reduced_body,re.S)
    for match_group in raw:
        yield MenuItem(match_group[0],match_group[1],match_group[2],match_group[3])

def formatJSONString(data: List[Tuple[str,List[MenuItem]]]) -> str:
    raise NotImplementedError

def getMealMenu(url: str) -> Iterable[Tuple[str,List[MenuItem]]]:
    whole_body = getWebsiteBody(url)
    for title, reduced_body in parseForStations(whole_body):
        yield (title, parseForItems(reduced_body))

def getJSONMealMenu(url: str):#url should be the link to today's brandywine or anteatery website for one specific meal
    return formatJSONString(getMealMenu(url))

if __name__ == "__main__":
    anteatery_url = "https://uci.campusdish.com/LocationsAndMenus/TheAnteatery"
    for station in getMealMenu(anteatery_url):
        print(station[0])
        for item in station[1]:
            print(item)
