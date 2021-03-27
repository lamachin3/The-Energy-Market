from multiprocessing import Process
import sysv_ipc, sys

key = 321

class SharingPlatform(Process):
    mq = None
    nb_houses = int

    def __init__(self, nb_houses):
        super().__init__()
        self.nb_houses = nb_houses
        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX) #crée une message queue 
        except:
            print("Message queue", key, "already exists, terminating.")
            sys.exit(1)

    def run(self):
        while True:
            if self.mq.current_messages == self.nb_houses: #attend que toutes les maisons aient envoyé un message
                data_rcvd = dict()
                while self.mq.current_messages != 0: #tant qu'il y a encore des messages à traiter
                    msg = self.mq.receive(type=-3)[0].decode() #traite tous les messages de type <= 3 en commençant par le type le plus petit (priorisation des échanges pour les policy 1 (energie perdu sinon))
                    msg_split = msg.split("_") #sépare le GAP du PID 
                    data_rcvd[msg_split[1]] = int(msg_split[0]) #enregistre les informations dans un dictionnaire

                data_send = self.processing(data_rcvd) #effectue les échanges entre les maisons puis renvoie l'energie restante après transaction dans un autre dictionnaire
                for i in data_send:
                    self.mq.send(str(data_send[i]).encode(), type=int(i)) #envoie la nouvelle valeur après échange à leur propriétaire à l'aide du PID

    def processing(self, rcvd_dict):
        needed_dict = dict()
        available_dict = dict()
        for i in rcvd_dict:
            if rcvd_dict[i] < 0: #besoin d'energie
                needed_dict[i] = abs(rcvd_dict[i]) #regroupe toutes les maisons qui ont besoin d'energie dans le dictionnaire needed_dict
            elif rcvd_dict[i] > 0: #surplus d'energie
                available_dict[i] = rcvd_dict[i] #regroupe toutes les maisons qui ont un surplus d'energie dans le dictionnaire needed_dict

        while needed_dict and available_dict: #tant qu'il y a des besoins ET des surplus d'energie
            key1, key2 = list(needed_dict.keys())[0], list(available_dict.keys())[0] #récupere la clé du premier élément de chaque dictionnaire
            val_need, val_avlb = needed_dict[key1], available_dict[key2] #récupere la valeur associée à cette clé
            if val_need == val_avlb: #échange parfait tous les deux n'ont ni surplus ni besoin
                needed_dict.pop(key1) #la maison de needed n'a plus de besoin
                available_dict.pop(key2) #la maison de available n'a plus d'energie 
            elif val_need < val_avlb: #comble le besoin mais il reste un surplus
                needed_dict.pop(key1) #la maison de needed n'a plus de besoin
                available_dict[key2] = val_avlb - val_need #calcul le surplus restant pour la maison de available
            else: #ne comble pas le besoin mais le réduit, la maison dans available donne tout ce qu'elle a 
                available_dict.pop(key2) #la maison de available n'a plus d'energie 
                needed_dict[key1] = val_need - val_avlb #calcul le besoin restant pour la maison de needed
        
        for i in rcvd_dict:
            rcvd_dict[i] = 0 #considérons que toutes les transactions ont conduit à un parfait échange
        
        if needed_dict: #il reste des besoins d'energie après échange
            for i in needed_dict:
                rcvd_dict[i] = -needed_dict[i] #rajoute les besoins restants après la transaction dans rcvd
        elif available_dict: #il reste des surplus d'energie après échange
            for i in available_dict:
                rcvd_dict[i] = available_dict[i] #rajoute les surplus d'energie restants après la transaction dans rcvd
        #else : echange parfait donc aucune action puisqu'il confirme l'hypothèse ligne 55
        return rcvd_dict
