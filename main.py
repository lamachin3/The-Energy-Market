import threading, random
from home import Home
from weather import Weather

if __name__ == "__main__":
    weather = Weather()
    temperature = weather.getSharedMem()
    weather_thread = threading.Thread(target= weather.genTemperature, args=())
    weather_thread.start()

    homes = []
    for i in range(3):
        homes.append(Home(random.randint(1,3), temperature))

    for home in homes:
        home.start()

    for home in homes:
        home.join()
    weather_thread.join()
    