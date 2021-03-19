
import os
import sys 
import time
import sysv_ipc

key = 666

def user():
    answer = 3
    while answer not in [1, 2]:
        print("1. to get current date/time")
        print("2. to terminate time server")
        answer = int(input())
    return answer

try:
    mq = sysv_ipc.MessageQueue(key)
except ExistentialError:
    print("Cannot connect to message queue", key, ", terminating.")
    sys.exit(1) 
    
t = user()

if t == 1:
    pid = os.getpid()
    m = str(pid).encode()
    mq.send(m)
    m, t = mq.receive(type = (pid + 3))
    dt = m.decode()
    print("Server response:", dt)
    
if t == 2:
    m = b""
    mq.send(m, type = 2)
