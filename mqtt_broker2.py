# -*- coding: utf-8 -*-

from queue import Queue
import noise_prot_interface
import sys, getopt
import time
from multiprocessing import Process, Queue
import queue

mssgsForTopic = {}
q = Queue(maxsize = 0)

class MQTTBroker:
    def __init__(self, username, password, server):
        self.username = username
        self.password = password
        self._noClients = 0
        self.server = server

 
    def pub_sub(self, msg):
        if 'publish' in msg:
            #print("Publisher connected")
            self.server.sendMessage("Publisher connected")
            msg = self.server.getMessage().split(":")
            topic = msg[0]
            v = msg[1]
            print("Received: {}".format(v))
            q.put(v)
            mssgsForTopic[topic] = q
            #print(q)
            #print(mssgsForTopic[topic].get())                                
           
        if "subscribe" in msg:
            #print("Subscriber connected")
            #self.server.sendMessage("Subscriber connected")
            topic = self.server.getMessage().split(":")[0]
            #while True:
            v = mssgsForTopic[topic].get()
            print(v)
            self.server.sendMessage(v)
            time.sleep(20)
                


    def listen(self, port):
        print("Starting Broker on port: {}".format(port))
        self.server.listen(interface='',port=port)

        msg = self.server.getMessage()
        if msg != "":
            if 'connect' in msg:
                try:
                    creds = msg.split(" ", 1)[1]
                    user = creds.split(":", 1)[0]
                    pwd = creds.split(':', 1)[1]

                    if self.username == user and self.password == pwd:
                        print("Connected")
                        self.server.sendMessage("Connected")
    
                        msg = self.server.getMessage()
                        while True:
                            self.pub_sub(msg)


                    else:
                        print("Unauthorized")
                           
                            
                except Exception as e:
                    print(e)
                    print("Provide credentials")
                    self.server.sendMessage("Provide credentials")


    def run_server(self, port):
        while True:
            self.listen(port)

def save_to_file(data, f_name):
        with open(f_name, 'w') as f:
            f.write(data)

    
def main():
    print("Args: %s" % (sys.argv))
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:t:u:p:",["interface=","tcpport=","username=","password="])
    except getopt.GetoptError:
        print ("%s -u <username> -p <password>" % (sys.argv[0]))
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("%s -u <username> -p <password>" % (sys.argv[0]))
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg



    server = noise_prot_interface.NoiseProtocolServer() 
    server2 =  noise_prot_interface.NoiseProtocolServer() 

    broker = MQTTBroker(username, password, server)
    broker2 = MQTTBroker(username, password, server2)

    p1 = Process(target=broker.run_server, args={2000})
    p1.start()
    broker2.run_server(2001)
    p1.join()
    #p2 = Process(target=broker2.run_server, args={2001})
    #ps = []
    #ps.append(p1)
    #ps.append(p2)
    #for p in ps:
        #p.start()

    #for p in ps:
        #p.join()




if __name__ == "__main__":
    main()
