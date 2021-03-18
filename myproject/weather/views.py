import requests
from django.shortcuts import render
from pyowm import OWM
import time
import datetime
import calendar

w_url = 'https://api.openweathermap.org/data/2.5/weather'
oc_url = 'https://api.openweathermap.org/data/2.5/onecall'
tz_url = 'http://api.timezonedb.com/v2.1/get-time-zone'
ctz_url = 'http://api.timezonedb.com/v2.1/convert-time-zone'

weather_key = 'dbab7c75a7f3830ad3b2cffc959d943d'
timezone_key = 'ZD24OOH9UGO6'

def home(response):
    return render(response, 'weather/home.html', {})

def favourites(response):
    return render(response, 'weather/favourites.html', {})

def search(request):
    def get_icon(id):
        if id[:2] == "01" or id[:2] == "02" or id[:2] == "10":
            return id
        else:
            return id[:2]

    if request.method == 'GET':
        #sets up city registry
        owm = OWM('dbab7c75a7f3830ad3b2cffc959d943d')
        location = request.GET.get('city')
        reg = owm.city_id_registry()

        if "," in location: #gets city data if country code is provided
            #splits city from country code
            city_and_country = location.split(",")
            city = city_and_country[0].strip()
            country = city_and_country[1].strip().upper()

            if len(country) == 2: #determines whether country code is valid(2 chaarcters long)
                city_id_name_country = reg.ids_for(city, country=country)
            else:
                return render(request, 'weather/search.html', {'location': location})
        else: #gets city data if country code is not provided
            city = location
            city_id_name_country = reg.ids_for(city)

        city_list = [(city[0],city[2]) for city in city_id_name_country]#create list of cities using id and country code

        #creates empty attribute list for the weather of the cities and sets iteration to 0
        city_attributes = []
        iteration = 0

        for city in city_list: #cycles through every city with the name and pulls basic info
            #requests API info on city
            params = {'APPID': weather_key, 'id': city[0], 'units': 'metric'}
            w = requests.get(w_url, params).json()

            ind =  len(w["weather"])-1 # determines which index to pull weather from(second is preffered but sometimes only first is avliable)

            #creates list of weather of city
            city_attributes.append({
                'name':w["name"],
                'country': w["sys"]["country"],
                'description':  w["weather"][ind]["description"],
                'temp': round(w["main"]["temp"]),
                'wind': round(w["wind"]["speed"]*3.6),
                'humidity': w["main"]["humidity"],
                'icon': get_icon(w["weather"][ind]["icon"]),
                'id': city[0]
            })

            if city[1] != w["sys"]["country"]: #determines whether ocuntry code is actually a state code
                city_attributes[iteration]['state'] = city[1]

            iteration += 1

        return render(request, 'weather/search.html', {
            'city_list': city_list,
            'location': location,
            'city_attributes': city_attributes,
        })

def weather(response, id):
    w_params = {'APPID': weather_key, 'id': id, 'units': 'metric'}
    w = requests.get(w_url, w_params).json()

    oc_params = {'APPID': weather_key, 'lat': w["coord"]["lat"], 'lon': w["coord"]["lon"], 'units': 'metric'}
    oc = requests.get(oc_url, oc_params).json()

    tz_params = {'key': timezone_key, 'format': 'json', 'by': 'position', 'lat': w["coord"]["lat"],
                 'lng': w["coord"]["lon"], }
    tz = requests.get(tz_url, tz_params).json()

    timezone = tz["abbreviation"]

    def get_icon(id):
        if id[:2] == "01" or id[:2] == "02" or id[:2] == "10":
            return id
        else:
            return id[:2]

    def format_time(time):
        if time[0:2] == "00": #between 00:00 and 00:59
            return "12" + time[2:5] + " AM"

        elif time[0] == '0' and time[1] != 0:#between 01:00 and 09:59
            return time[1:5] + " AM"

        elif int(time[:2]) > 9 and int(time[:2]) < 13 : #between 10:00 and 12:59
            if time[:2] == "12":
                return time[0:5] + " PM"
            else:
                return time[0:5] + " AM"

        elif int(time[0:2]) > 12 and int(time[0:2]) < 24: #between 13:00 and 23:59
            return str(int(time[:2]) - 12) + time[2:5] + " PM"

        elif int(time[0:2]) > 23: #24:00 and higher(next days)
            hour = str(int(time[0:2])-24)
            if hour == "0": #between 24:00 and 24:59
                hour = "00"
            elif len(hour) == 1: #between 25:00 and 33:59
                hour = "0" + hour
            return format_time(hour + time[2:5])# 34:00+

    def convert_unix(unix_time, local_timezone):
        time.sleep(1)
        params = {'key': timezone_key, 'format': 'json', 'from': 'UTC', 'to': local_timezone,'time': unix_time}
        cu = requests.get(ctz_url, params).json()
        return datetime.datetime.utcfromtimestamp(cu["toTimestamp"]).strftime('%Y-%m-%d %H:%M:%S')

    def get_alerts():
        if oc.get("alerts"):
            if "warning" in oc["alerts"][0]["event"].lower():
                return oc["alerts"][0]["event"].title()
            else:
                return oc["alerts"][0]["event"].title() + " Warning"
        else:
            return None

    def date(start, days_after):
        day = start+days_after
        if day > 6:
            day-=7
        return day

    def weather_short():
        ind = len(w["weather"]) - 1# determines which index to pull weather from(second is preffered but sometimes only first is avliable)
        return {
            'icon': get_icon(w["weather"][ind]["icon"]),
            'temp': str(round(oc["current"]["temp"])) + "°",
            'description': w["weather"][ind]["description"].title(),
            'high': str(round(oc["daily"][3]["temp"]["max"])) + "°",
            'low': str(round(oc["daily"][3]["temp"]["min"])) + "°",
            'alerts': get_alerts(),
        }

    def weather_long():
        #converts wind direction from dehrees to comapss directions
        deg = int((oc["current"]["wind_deg"] / 22.5) + .5)
        dir = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

        return {
            'sunrise': format_time(convert_unix(oc["current"]["sunrise"], timezone)[11:16]),
            'sunset': format_time(convert_unix(oc["current"]["sunset"], timezone)[11:16]),
            'humidity': str(w["main"]["humidity"]) + "%",
            'dew_point': str(round(oc["current"]["dew_point"])) + "°",
            'pressure': str(oc["current"]["pressure"]) + " hPa",
            'uvi': str(round(oc["current"]["uvi"])),
            'visibility': str(round(oc["current"]["visibility"] / 1000, 2)) + " km",
            'wind': dir[(deg % 16)] + " " + str(round(w["wind"]["speed"] * 3.6)) + " km/h",
            'high': str(round(oc["daily"][3]["temp"]["max"])) + "°",
            'low': str(round(oc["daily"][3]["temp"]["min"])) + "°",
            'feels_like': str(round(oc["current"]["feels_like"])) + "°",
        }

    def hourly():
        current_hour = tz["formatted"][11:13]
        hourly_list = []
        for i in range(1, 25):
            hour = str(int(current_hour)+i)
            if len(hour) == 1:
                hour = "0" + hour

            hourly_list.append({
                'time': format_time(hour + ":00"),
                'icon': get_icon(oc["hourly"][i]["weather"][0]["icon"]),
                'temp': str(round(oc["hourly"][i]["temp"])) + "°",
            })
        return hourly_list

    def daily():
        daily_list=[]
        weekDays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        year, month, day = (int(i) for i in tz["formatted"][:10].split('-'))
        today = calendar.weekday(year, month, day)
        for i in range(1,8):
            daily_list.append({
                'date': weekDays[date(today, i)],
                'icon': get_icon(oc["daily"][i]["weather"][0]["icon"]),
                'high': str(round(oc["daily"][i]["temp"]["max"])) + "°",
                'low': str(round(oc["daily"][i]["temp"]["min"])) + "°"
            })
        return daily_list

    #returns information
    return render(response, "weather/city_weather.html", {
        'id': w["id"],
        'city':w['name'],
        'country': tz["countryName"],
        'timezone': timezone,
        'time': format_time(tz["formatted"][11:16]),
        'weather_short': weather_short(),
        'weather_long': weather_long(),
        'hourly': hourly(),
        'daily': daily(),
    })

def alerts(request, id):
    w_params = {'APPID': weather_key, 'id': id, 'units': 'metric'}
    w = requests.get(w_url, w_params).json()

    oc_params = {'APPID': weather_key, 'lat': w["coord"]["lat"], 'lon': w["coord"]["lon"], 'units': 'metric', 'excludes':'current,minutely,hourly,daily'}
    oc = requests.get(oc_url, oc_params).json()

    return render(request, "weather/alerts.html", {
        'city': w['name'],
        'sender': oc["alerts"][0]["sender_name"],
        'description': oc["alerts"][0]["description"],
    })