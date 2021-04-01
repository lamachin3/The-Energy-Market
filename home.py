from multiprocessing import Process
import random
import math
import sysv_ipc
import time, os
 
key_market = 123 #clé de la message queue du market
key_share = 321 #clé de la messager queue du partage

class Home(Process):

    cons, prod, policy = int, int, int
    balance = 0 #Si balance > 0 plus d'achat que de vente et vice versa
    stop = None
    temperature = None
    barrier = None
    mq_market, mq_share = None, None
    recap = dict() #"day_n : [gap_debut, gap_share]" 

    def __init__(self, policy, shrdMem, barrier, stop):
        super().__init__()
        self.policy = policy
        self.temperature = shrdMem
        self.barrier = barrier
        self.stop = stop
        try:
            self.mq_market = sysv_ipc.MessageQueue(key_market) #Connexion à une message queue pour communiquer avec le market
            self.mq_share = sysv_ipc.MessageQueue(key_share) #Connexion à une message queue pour communiquer avec les autres maisons
        except:
            print("Cannot connect to message queue, terminating.")
            exit(1)
        

    def run(self):
        self.barrier.wait()
        while not self.stop.value:
            self.getCons()
            self.getProd()
            self.buy_or_sell(self.mq_market, self.share(self.mq_share)) #Partage entre toutes les maisons puis transactions avec le marché
            self.barrier.wait()
        
        for i in self.recap:
            print("Day_" + str(repr(i)), repr(self.recap[i][0]).rjust(4), repr(self.recap[i][1]).rjust(4), end='\t\t')
        print("\n")

    #calcul de la consommation de la maison
    def getCons(self): 
        self.cons = round(10 + ((self.temperature.value - 20)/4)**2 + random.randint(-5, 5))

    #calcul de la production de la maison 
    def getProd(self):
        self.prod = round(2*self.temperature.value + random.randint(-5, 5))
        if self.prod < 0:
            self.prod = 0

    #achat et vente sur le marché
    def buy_or_sell(self, mq_market, gap):
        encd_gap = str(abs(gap)).encode()
        if gap > 0:
            mq_market.send(encd_gap, type = 1) #type 1 = demande de vente d'energie sur le marché
        elif gap < 0:
            mq_market.send(encd_gap, type=2) #type 2 = demande d'achat d'energie sur le marché

    #partage des ressources avec les autres maisons
    def share(self, mq_share):
        gap = self.prod - self.cons #calcul du reste de l'energie après consommation
        if self.policy == 2 and gap > 0:
            msg = "0_" + str(os.getpid()) # pas de partage pour la policy 2
        else:
            msg = str(gap) + "_" + str(os.getpid())
        msg = msg.encode()
        
        mq_share.send(msg, type=self.policy)
        msg_rcvd = mq_share.receive(type=os.getpid())[0].decode() 
        if self.policy == 2 and gap > 0:
            msg_rcvd = gap #réatribution de l'écart non mis sur le partage
        self.recap[len(self.recap) + 1]=(gap, int(msg_rcvd))
        return int(msg_rcvd) #retourne le reste à mettre sur le marché
