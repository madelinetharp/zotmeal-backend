from api.index import scrape_menu_to_dict
import json

if __name__=="__main__":
    with open("eatery_dummy.json","w",encoding="utf-8") as f:
        data = scrape_menu_to_dict("anteatery")
        json.dump(data,f,ensure_ascii=False)
    with open("brandy_dummy.json","w",encoding="utf-8") as f:
        data = scrape_menu_to_dict("brandywine")
        json.dump(data,f,ensure_ascii=False)