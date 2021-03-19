from multiprocessing import Value

class Weather:

    temperature = Value('i', 0)

    def getTemperature(self):        
        return self.temperature.value #value à enlever por shared memory

    def setTemperature(self, n):
        self.temperature.value = n

if __name__ == "__main__":
    weather = Weather()
    print(weather.getTemperature())
    weather.setTemperature(12)
    print(weather.getTemperature())