from http.server import BaseHTTPRequestHandler#imported to have an http endpoint
import json#imported to format dict as json string
import urllib.parse #imported to help parsing url componenets
import traceback#for error handling
import os#imported to get environment variables
from .location_management import is_valid_location
from .json_reader import get_diner_json


USE_CACHE = bool(os.getenv("USE_CACHE"))

print("Using cache" if USE_CACHE else "Not using cache")

# TODO: need to clear Firebase cache of outdated JSONS, should probably implement timer
# e.g. force refresh of cache every hour
USE_CACHE = False

if USE_CACHE:
    #ideally this firebase stuff would be in a separate file but idk how to get vercel to let me import my own files into eachother
    import firebase_admin#https://firebase.google.com/docs/database/admin/start
    from firebase_admin import credentials
    from firebase_admin import db
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_ADMIN_CREDENTIALS")))

    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
    })

    def get_db_reference(location: str, meal: int, date: str) -> db.Reference:
        if meal is None:
            meal = get_current_meal()

        if date is None:
            irvine_time = get_irvine_time()
            date = f"{irvine_time.tm_mon}/{irvine_time.tm_mday}/{irvine_time.tm_year}"

        modified_datestring = date.replace("/","|")
        
        # .get() returns None if nothing created
        return db.reference(f"{location}/{modified_datestring}/{meal}")


class InvalidQueryException(Exception):
    pass

class NotFoundException(Exception):
    pass

# to implement redirects see this: https://stackoverflow.com/questions/22701544/redirect-function-with-basehttprequesthandler
# redirects could be useful to just send the request straight to firebase

class handler(BaseHTTPRequestHandler):

    def process_response(self, status_code: int, header: tuple, data) -> None:
        ''' 
        Given a status_code, header, and data, forward the information to the client
        '''

        self.send_response(status_code)
        self.send_header(*header)
        self.end_headers()
        self.wfile.write(data.encode())

    def __read_get(self) -> ('path', 'params', 'query'):
        '''
        If a get request is made, validate the path, params, and raw query
        valid   : return the 3 relevant values in a tuple
        invalid : raise NotFoundException
        '''
        _, _, path, params, raw_query, _ = urllib.parse.urlparse("//"+self.path)#prepending the // separates netloc and path

        if not path == "/api" or path == "/api/":
            raise NotFoundException

        query = urllib.parse.parse_qs(raw_query)

        return path, params, query


    def __validate_query_location(self, query) -> 'location':
        '''
        Given a query, verify that a location is present and valid
        valid   : return the location in lowercase
        invalid : raise InvalidQueryException
        '''

        if 'location' not in query:
            raise InvalidQueryException('No location query parameter specified')
        
        location = query['location'][0]

        if not is_valid_location(location):
            raise InvalidQueryException(f'The location specified is not valid. Valid locations: {list(location_management.LOCATION_INFO.keys())}')

        return location

    def __validate_query_meal_date(self, query) -> ('meal', 'date'):
        '''
        Given a query, check if there is a valid combination of meal_id and date
        valid   : return the two values in a tuple
        invalid : raise InvalidQueryException
        '''

        meal = int(query['meal'][0]) if 'meal' in query else None

        date = query['date'][0] if 'date' in query else None # note: data gets decoded by urllib, so it will contain slashes.

        if meal is None and not date is None:
            raise InvalidQueryException('You can\'t provide the date without the meal (not implemented in the server).')

        return meal, date

    def do_GET(self):
        '''
        Given a get request for food, respond accordingly
        '''

        try:
            path, params, query = self.__read_get()
            location            = self.__validate_query_location(query)
            meal, date          = self.__validate_query_meal_date(query)

            if USE_CACHE:
                print(f'date from query params: {date}')
                db_ref = get_db_reference(location, meal, date)

                db_data = db_ref.get()

                if(db_data is None):
                    data = get_diner_json(location, meal, date)
                    db_ref.set(data)

                else:
                    data = db_data
            else:
                data = get_diner_json(location, meal, date)
                    
            self.process_response(
                    status_code = 200, 
                    header     = ('Content-type', 'application/json'), 
                    data        = json.dumps(data, ensure_ascii = False, indent = 4)
            )

        except NotFoundException:
            self.process_response(
                    status_code = 404, 
                    header     = ('Content-type', 'text/plain'), 
                    data        = 'Invalid path. The only one available is /api'
            )

        except InvalidQueryException as e:
            self.process_response(
                status_code = 400, 
                header     = ('Content-type', 'text/plain'), 
                data        = f'Invalid query parameters. Details: {e}'
        )
            
        except Exception as e:
            traceback.print_exc()
            self.process_response(
                    status_code = 500, 
                    header     = ('Content-type', 'text/plain'), 
                    data        = f'Internal Server Error. Raise an issue on the github repo: https://github.com/EricPedley/zotmeal-backend. Details: {e}'
            )

