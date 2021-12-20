import time
import calendar

# Default offset for Irvine from GMT (GMT-8 = -28800 seconds)
IRVINE_OFFSET = -28800

# Helper functions
def _lower_first_letter(s: str) -> str:
    'Lowercase the first letter of a string'
    return s[0].lower() + s[1:]

def _find_icon(icon_property: str, food_info: dict) -> bool:
    'Return true if the badge can be found in any of the dietary information images'
    return any(map(lambda diet_info: icon_property in diet_info["IconUrl"], food_info["DietaryInformation"]))

def _normalize_time(time_struct: time.struct_time) -> int:
    'Formats the time into a 4-digit integer, controls how time is represented in API'
    return int(f'{time_struct.tm_hour}{time_struct.tm_min:02}')

def _read_schedule_UTC(utc_time: str) -> int:
    '''
    Convert utc time string from UCI API to time.struct_time,
    convert struct to seconds since epoch, subtract 8 hours, and normalize to
    '''
    gmt_struct = time.strptime(utc_time, '%Y-%m-%dT%H:%M:%S.0000000')
    local_struct = time.gmtime(calendar.timegm(gmt_struct) + IRVINE_OFFSET)
    return _normalize_time(local_struct)

def _get_irvine_time():
    'Return the local time in normalized format'
    local_time = time.gmtime(time.time() + IRVINE_OFFSET)
    return local_time
