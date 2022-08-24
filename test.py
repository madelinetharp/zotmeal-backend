from api.parsing import make_response_body
import json

if __name__=="__main__":
    with open('eatery_dummy.json', 'w', encoding = 'utf-8') as f:
        data = make_response_body('anteatery')
        json.dump(data, f, ensure_ascii = False, indent = 4)

    with open('brandy_dummy.json', 'w', encoding = 'utf-8') as f:
        data = make_response_body('brandywine')
        json.dump(data, f, ensure_ascii = False, indent = 4)
