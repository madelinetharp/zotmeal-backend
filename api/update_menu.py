'''
    Returns a list of bool, presences, where presences[i] denotes whether or not keywords[i] is present in test_string
    i.e presences[i] = keywords[i] in test_string
'''
def findMultiple(test_string: str, keywords: "list[str]") -> "list[bool]":#list[str] doesn't need quotes on python >=3.9
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


#regex for each station: r"station-header-title.*?>(.*?)<.*?<\/div>\s+<\/div>\s+</div>"
# full match: everything about the menu station (including items). Run second regex on this string for each station.
# group 1: the name of the menu station
#regex for each item within a station: r"menu__item.*?#\">(.*?)<.*?__calories\">(.*?) Calories.*?__content\">(.*?)<(.*?)<\/ul>"
# full match: everything about the item
# group 1: name of item
# group 2: calories of item
# group 3: description of item
# group 4: remaining info, which includes categories like EatWell or Vegan. Run a find for EatWell, Vegan, Vegetarian, etc. for this one.
