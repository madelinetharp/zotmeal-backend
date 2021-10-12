from typing import List, Tuple, Iterable
#typing annotations. I think python >=3.9 doesn't need this import, but using older version for better compatibility with cloud platforms.
'''
    Returns a list of bool, presences, where presences[i] denotes whether or not keywords[i] is present in test_string
    i.e presences[i] = keywords[i] in test_string
'''
from typing import NamedTuple

def findMultiple(test_string: str, keywords: List[str]) -> List[bool]:#list[str] doesn't need quotes on python >=3.9
    presences = [False]*len(keywords)
    traversal_list = [[i,keywords[i]] for i in range(len(keywords))]
    for char in test_string:
        for i, position_keyword_list in enumerate(traversal_list):
            #python sucks because I can't unpack position_keyword_list[0] as an integer reference without cheesy shit like wrapping it in a list
            if presences[i]:
                continue
            if char==position_keyword_list[1][position_keyword_list[0]]:
                position_keyword_list[0]+=1
            else:
                position_keyword_list[0]=0
            if position_keyword_list[0]==len(position_keyword_list[1]):
                presences[i] = True
    return presences

# print(findMultiple("this string contains many words",["string","contains","bannaa","container"]))

def getWebsiteBody(url: str) -> str:#returns the html content returned by a GET request to the specified URL
    raise NotImplementedError

def parseForStations(body: str) -> List[Tuple[str,str]]:#takes the html body of the dining website and returns a list of tuples, each containing the station's name and the html content for that station
    #regex for each station: r"station-header-title.*?>(.*?)<.*?<\/div>\s+<\/div>\s+</div>"
    # full match: everything about the menu station (including items). Run second regex on this string for each station.
    # group 1: the name of the menu station
    raise NotImplementedError

#using namedtuples because they're like structs, and MenuItem doesn't need methods
MenuItem = NamedTuple("MenuItem",[("name",str),("calories",int),("description",str),("categories","list[bool]")])

def parseForItems(reduced_body: str) -> List[MenuItem]:#takes the html body of each station and returns a list of the menu items in that station
    #regex for each item within a station: r"menu__item.*?#\">(.*?)<.*?__calories\">(.*?) Calories.*?__content\">(.*?)<(.*?)<\/ul>"
    # full match: everything about the item
    # group 1: name of item
    # group 2: calories of item
    # group 3: description of item
    # group 4: remaining info, which includes categories like EatWell or Vegan. Run a find for EatWell, Vegan, Vegetarian, etc. for this one.
    raise NotImplementedError

def formatJSONString(data: List[Tuple[str,List[MenuItem]]]) -> str:
    raise NotImplementedError

def getMealMenu(url: str) -> Iterable[Tuple[str,List[MenuItem]]]:
    whole_body = getWebsiteBody(url)
    for title, reduced_body in parseForStations(whole_body):
        yield (title, parseForItems(reduced_body))

def getJSONMealMenu(url: str):#url should be the link to today's brandywine or anteatery website for one specific meal
    return formatJSONString(getMealMenu(url))

if __name__ == "__main__":
    pass
