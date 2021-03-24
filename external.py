from multiprocessing import Process

class External(Process):

    def __init__(self):
        print("External declared")