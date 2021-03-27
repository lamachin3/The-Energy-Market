from multiprocessing import Process
import random
import math
import sysv_ipc
import time, os
 
key_market = 123 #clé de la message queue du market
key_share = 321 #clé de la messager queue du partage

class Home(Process):

    cons, prod, policy, temperature = int, int, int, None
    #accounting = {"sold": [], "bought": []}

    def __init__(self, policy, shrdMem):
        super().__init__()
        self.policy = policy
        self.temperature = shrdMem

    def run(self):
        try:
            mq_market = sysv_ipc.MessageQueue(key_market) #Création d'une message queue pour communiquer avec le market
        except:
            print("Cannot connect to message queue", key_market, ", terminating.")
            exit(1)
        
        mq_share = sysv_ipc.MessageQueue(key_share) #Création d'une message queue pour communiquer avec les autres maisons

        t0 = time.time()
        while True:
            t1 = time.time()
            if t1-t0 > 10:
                self.getCons()
                self.getProd()
                self.buy_or_sell(mq_market, self.share(mq_share))
                t0 = t1  

    #calcul de la consommation de la maison
    def getCons(self): 
        #self.cons = round(100 + ((self.temperature.value - 20)/2)**2 + random.randint(-20, 20))
        self.cons = random.randint(0, 200) 
        #print("Conso : {} - {}".format(self.cons, os.getpid()))

    #calcul de la production de la maison 
    def getProd(self):
        #self.prod = round(8*self.temperature.value + random.randint(-50, 50))
        self.prod = random.randint(0, 100)
        if self.prod < 0:
            self.prod = 0
        #print("Prod : {} - {}".format(self.prod, os.getpid()))

    #achat et vente sur le marché
    def buy_or_sell(self, mq_market, gap):
        encd_gap = str(abs(gap)).encode()
        if gap > 0:
            mq_market.send(encd_gap, type = 1) #demande de vente d'energie sur le marché
        elif gap < 0:
            mq_market.send(encd_gap, type=2) #demande d'achat d'energie sur le marché

    #partage des ressources avec les autres maisons
    def share(self, mq_share):
        gap = self.prod - self.cons #calcul du reste de l'energie après consommation
        print("gap", gap, "\tpid", os.getpid())
        if self.policy == 2 and gap > 0:
            msg = "0_" + str(os.getpid()) # pas de partage
        else:
            msg = str(gap) + "_" + str(os.getpid()) #création du message pour la message queue avec l'écart et le PID sous la forme (GAP_PID)
        msg = msg.encode()
        
        mq_share.send(msg, type=self.policy) #envoi du message de type = policy
        msg_rcvd = mq_share.receive(type=os.getpid())[0].decode() #réception du message de type = PID
        if self.policy == 2 and gap > 0:
            msg_rcvd = gap #réatribution de l'écart non mis sur le partage 
        return int(msg_rcvd)
