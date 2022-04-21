#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

import noise_prot_interface
import socket
import sys, getopt
import time


def read_file(f_name):
    with open(f_name, 'r') as f:
        return f.read()


def cpu_temp():
    return read_file('/sys/class/thermal/thermal_zone0/temp')

class MQTTClient:
    def __init__(self, username, password):
        self.salt = read_file('salt')
        self.password = password
        self.client = noise_prot_interface.NoiseProtocolClient()
        self.username = username

    def cli(self, cli, topic, port):
        self.client.connect(destination='localhost', port= port)
        print(str(self.password))
        self.client.sendMessage('connect ' + str(self.username) + ':' + str(self.password))
        msg = self.client.getMessage()
        print(msg)

        if msg == 'Connected':
            if cli == 'pub':
                self.client.sendMessage('publish')
                #print(self.client.getMessage())
                while True:
                    print(cpu_temp())
                    self.client.sendMessage("{}:{}".format(topic, cpu_temp()))
                    time.sleep(15)
            elif cli == 'sub':
                self.client.sendMessage('subscribe')
                print(self.client.getMessage())

        else:
            return self.client.getMessage()



def main():
    print("Args: %s" % (sys.argv))
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:u:p:t:c:n:",["username=","password=","topic=", "client=","n="])
    except getopt.GetoptError:
        print ("%s -u <username> -p <password> -t <topic> -c <pub/sub> -n <portnu>" % (sys.argv[0]))
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("%s -u <username> -p <password> -t <topic> -c <pub/sub> -n <portnu>" % (sys.argv[0]))
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-t", "--topic"):
            topic = arg
        #TODO pub sub arg
        elif opt in ("-c", "--client"):
            cli = arg
        elif opt in ("-n", "--port"):
            port = arg

    s_ip = 'localhost'
    while True:
        msg = MQTTClient(username, password).cli(cli, topic, int(port))
    print(msg)

main()
