import requests
from django.shortcuts import render
from django.conf import settings
from datetime import datetime

# Create your views here.
def home(request):
    weather_data = {}
    forecast_data = []
    search_history = request.session.get('search_history', [])

    if request.method == 'POST':
        api_key = settings.OPENWEATHER_API_KEY
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        city = request.POST.get('city')

        # Debugging: Check if lat, lon, and city are coming correctly
        print(f"City: {city}")
        print(f"Latitude: {lat}")
        print(f"Longitude: {lon}")

        # 1. Get coordinates if not provided
        if not lat or not lon:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
            geo_response = requests.get(geo_url)
            if geo_response.status_code == 200 and geo_response.json():
                geo_data = geo_response.json()[0]
                lat = geo_data['lat']
                lon = geo_data['lon']
            else:
                return render(request, 'weather/home.html', {
                    'weather': {'error': 'City not found.'},
                    'history': search_history
                })

        # 2. Get current weather using lat/lon
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        weather_response = requests.get(weather_url)

        if weather_response.status_code == 200:
            data = weather_response.json()
            weather_data = {
                'city': data['name'],
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'wind': data['wind']['speed']
            }
            if not city:
                reverse_geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
                reverse_response = requests.get(reverse_geo_url)
                if reverse_response.status_code == 200 and reverse_response.json():
                    city = reverse_response.json()[0]['name']


            if city and city not in search_history:
                search_history.insert(0, city)
                search_history = search_history[:5]
                request.session['search_history'] = search_history

            # 3. Get 7-day forecast from One Call API
            onecall_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={api_key}&units=metric"
            onecall_response = requests.get(onecall_url)
            if onecall_response.status_code == 200:
                onecall_data = onecall_response.json()
                forecast_data = onecall_data['daily'][:7]  # next 7 days
                print("Forecast Data:", forecast_data)  # 🔍 DEBUG

        else:
            weather_data = {'error': 'Weather data not found.'}

    return render(request, 'weather/home.html', {
        'weather': weather_data,
        'forecast': forecast_data,
        'history': search_history
    })
