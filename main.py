import threading, random, os
from home import Home
from weather import Weather
from market import Market
from sharing_platform import SharingPlatform

# ipcrm -Q 123; ipcrm -Q321; python main.py

if __name__ == "__main__":
    nb_houses = 3
    weather = Weather()
    temperature = weather.getSharedMem()
    weather_thread = threading.Thread(target= weather.genTemperature, args=())
    weather_thread.start()

    market = Market(temperature)
    market.start()

    sharing_platform = SharingPlatform(nb_houses)
    sharing_platform.start()


    homes = []
    for i in range(nb_houses):
        #homes.append(Home(random.randint(1,3), temperature))
        homes.append(Home(i+1, temperature))

    for home in homes:
        home.start()

    for home in homes:
        home.join()

    market.join()
    sharing_platform.join()
    weather_thread.join()
