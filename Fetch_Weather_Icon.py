import pygame
import requests
from PIL import Image
from io import BytesIO

def get_API_key():
    API_KEY = 'your_api_key_here'  # Replace with your actual API key
    return API_KEY

def get_weather_data(city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={get_API_key()}"
    response = requests.get(url)
    data = response.json()
    return data

def fetch_weather_icon(icon_code):
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    response = requests.get(icon_url)
    img = Image.open(BytesIO(response.content))
    return img

def fetch_weather_icon2(icon_code):
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    response = requests.get(icon_url)
    img = Image.open(BytesIO(response.content))
    # Convert the PIL Image to a format pygame can use
    img_data = img.tobytes()  # Obtain raw image data from the PIL image
    img_mode = img.mode  # Get the mode ('RGB', 'RGBA')
    img_size = img.size  # Get image size as (width, height)
    # Create a Surface from the raw image data
    return pygame.image.fromstring(img_data, img_size, img_mode)


def load_weather_pattern(city_name):
    weather_data = get_weather_data(city_name)
    icon_code = weather_data['weather'][0]['icon']  # Extract the icon code
    icon_image = fetch_weather_icon(icon_code)
    return icon_image
