import threading, random, os, time, multiprocessing, sysv_ipc
import argparse
from home import Home
from weather import Weather
from market import Market
from sharing_platform import SharingPlatform
from multiprocessing import Value

# ipcrm -Q 123; ipcrm -Q 321; python main.py

if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage='main.py -n NB_HOUSES -d NB_DAYS -t TEMPERATURE -p NB_POLICY_1 NB_POLICY_2 NB_POLICY_3')
    parser.add_argument('-n', "--houses",  type=int, metavar='NB_HOUSES', help="number of houses to create", required=True)
    parser.add_argument('-d', "--days", type=int, metavar='NB_DAYS', help="number of days to perform", required=True)
    parser.add_argument('-t', "--temperature", type=int, metavar='TEMPERATURE', help="initial temperature", required=True)
    parser.add_argument('-p', "--policies", nargs="+", help="number of houses for each policy")
    args = parser.parse_args()

    nb_days = int(args.days)
    nb_houses = int(args.houses)
    temperature = int(args.temperature)
    if args.policies:
        sum = 0
        for i in args.policies:
            sum += int(i)
        if sum != nb_houses:
            print("Number of houses doesn't match the policies. Exiting the cool program.")
            exit(1)
    


    stop = Value('b', False)
    barrier = multiprocessing.Barrier(4 + nb_houses) # 1 main + 1 weather + 1 market + 1 sharing platform + N home
    weather = Weather(barrier, stop)
    shrd_temp = weather.getSharedMem()
    shrd_temp.value = temperature

    weather_thread = threading.Thread(target= weather.genTemperature, args=())
    weather_thread.start()

    market = Market(shrd_temp, barrier, stop)
    market.start()

    sharing_platform = SharingPlatform(args.houses, barrier, stop)
    sharing_platform.start()


    homes = []
    if not args.policies:
        for i in range(args.houses):
            homes.append(Home(random.randint(1,3), shrd_temp, barrier, stop))
    else:
        policy = 1
        for i in args.policies:
            i = int(i)
            for j in range(i):
                homes.append(Home(policy, shrd_temp, barrier, stop))
            policy += 1


    for home in homes:
        home.start()

    print("\n--- Journée 1 ---\n")
    barrier.wait()
    t0 = time.time()
    cpt = 1 
    while True and cpt<nb_days:
        t1 = time.time()           
        if t1-t0 > 3:
            print("\n--- Journée {} ---\n".format(cpt + 1))
            barrier.wait()
            #print(barrier.n_waiting)
            cpt += 1
            t0 = t1

    while barrier.n_waiting < barrier.parties - 1:
        pass
    print("\n")
    stop.value = True
    barrier.wait()

    for home in homes:
        home.join()

    market.join()
    sharing_platform.join()
    weather_thread.join()
    print("\nYour favorite Energy Market Simulator is over....")
