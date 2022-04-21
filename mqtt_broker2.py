#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

from queue import Queue
import noise_prot_interface
import sys, getopt
import time

mssgsForTopic = {}

class MQTTBroker:
    def __init__(self, username, password, server):
        self.username = username
        self.password = password
        self._noClients = 0
        self.q = Queue(maxsize = 0)
        self.server = server

 
    def pub_sub(self, msg):
        if 'publish' in msg:
            print("Publisher connected")
            self.server.sendMessage("Publisher connected")
            while True:
                msg = self.server.getMessage().split(":")
                topic = msg[0]
                v = msg[1]
                self.q.put(v)
                mssgsForTopic[topic] = self.q
                print(mssgsForTopic[topic].get())
                                
           
        elif "subscribe" in msg:
            print("Subscriber connected")
            self.server.sendMessage("Publisher connected")
            while True:
                    msg = mssgsForTopic[topic].get()
                    self.server.sendMessage(msg)


    def listen(self, port):
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
    broker = MQTTBroker(username, password, server)
    while True:
        broker.listen(2000)


if __name__ == "__main__":
    main()
