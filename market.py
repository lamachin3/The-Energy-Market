from multiprocessing import Process, Value
import concurrent.futures
import sysv_ipc, signal
import sys, os, time, random

key = 123

class Market(Process):
    temperature = None
    barrier = None
    stop = None
    accounting = float
    internal_factors = {"energy_balance": 0, "temperature": 0}
    external_factors = {"storm": 0, "fuel_shortage": 0}
    price = int
    mq = None
    new_day = Value('i', 0)

    def __init__(self, shrdMem, barrier, stop):
        super().__init__()
        self.temperature = shrdMem
        self.barrier = barrier
        self.stop = stop
        self.price = 0.145
        self.prices_hist = []
        self.accounting = 0

        signal.signal(signal.SIGUSR1, self.handler)
        signal.signal(signal.SIGUSR2, self.handler)

        external_proc = Process(target=self.external_worker, args=(self.new_day,)) #process fils external
        external_proc.start()

        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
        except:
            print("Message queue", key, "already exsits, terminating.")
            sys.exit(1)
    
    def handler(self, sig, frame):
        if sig == signal.SIGUSR1:
            self.external_factors["storm"] = 1
            with open('storm.txt','r') as f:
                print(f.read())
        
        if sig == signal.SIGUSR2:
            self.external_factors["fuel_shortage"] = 1
            with open('fuel.txt','r') as f:
                print(f.read())

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers = 3) as executor:
            while not self.stop.value:
                msg, t = None, None
                while msg == None and not self.stop.value:  #attend de recevoir un message dans la message
                    try:
                        msg, t = self.mq.receive(block=False) #non bloquant car on veut détecter si self.stop.value passe à TRUE
                    except:
                        msg = None
                if self.stop.value:
                    break
                data = int(msg.decode())

                if self.new_day.value == 1: #nouvelle journée
                    self.set_price()
                    self.new_day.value = 0

                if t == 1:
                    executor.submit(self.buy_energy, data) #thread pour que le marché achète de l'energie
                elif t == 2:
                    executor.submit(self.sell_energy, data) #thread pour que le marché vende de l'energie

        while self.mq.current_messages != 0:
            pass 
        self.mq.remove()
        print("Market prices history:", self.prices_hist)
    
    def sell_energy(self, qty):
        self.internal_factors["energy_balance"] -= qty
        self.accounting -= self.price * qty
        print("Selling {} to house for {}€ - current price: {}".format(qty, round(self.price * qty, 3), round(self.price, 3)))

    def buy_energy(self, qty):
        self.internal_factors["energy_balance"] += qty
        self.accounting += self.price * qty
        print("Buying {} from house for {}€ - current price: {}".format(qty, round(self.price * qty, 3), round(self.price, 3)))

    def set_price(self):
        self.internal_factors["temperature"]  = self.temperature.value
        gamma = 0.99
        alpha = [-0.0001, -0.001]
        beta = [0.002, 0.002]
        self.price = self.price * gamma

        for key in self.internal_factors:
            index = list(self.internal_factors).index(key)
            self.price += alpha[index] * self.internal_factors[key]
        
        for key in self.external_factors:
            index = list(self.external_factors).index(key)
            self.price += beta[index] * self.external_factors[key]

        self.prices_hist.append(round(self.price, 2))
        self.internal_factors["energy_balance"] = 0
            
        
    def external_worker(self, new_day):
        self.barrier.wait()
        p1, p2 =  0.95, 0.95
        while not self.stop.value:
            new_day.value = 1

            for i in self.external_factors:
                self.external_factors[i] = 0

            if random.random() > p1:
                os.kill(os.getppid(), signal.SIGUSR1)
                p1 = 0.95
            else:
                p1 = p1**2

            if random.random() > p2:
                os.kill(os.getppid(), signal.SIGUSR2)
                p2 = 0.95
            else:
                p2 = p2**2
            self.barrier.wait()
