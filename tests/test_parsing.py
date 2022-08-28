from api.parsing import make_response_body
import json

def test_no_crash():
    anteatery_data = make_response_body('anteatery')
    print(json.dumps(anteatery_data, ensure_ascii = False, indent = 4))

    brandywine_data = make_response_body('brandywine')
    print(json.dumps(brandywine_data, ensure_ascii = False, indent = 4))
