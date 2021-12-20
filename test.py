from api.index import scrape_menu_to_dict
import json

if __name__=="__main__":
    with open("eatery_dummy.json", "w", encoding = "utf-8") as f:
        data = scrape_menu_to_dict("anteatery", date = "01/20/2022")
        json.dump(data, f, ensure_ascii = False, indent = 4)

    with open("brandy_dummy.json", "w", encoding = "utf-8") as f:
        data = scrape_menu_to_dict("brandywine", date = "01/20/2022")
        json.dump(data, f, ensure_ascii = False, indent = 4)
