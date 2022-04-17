#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

import noise_prot_interface
from scapy.contrib.mqtt import *
from scapy.all import *
from mqtt_broker import Credentials
import socket

def read_file(f_name):
    with open(f_name, 'r') as f:
        return f.read()

class MQTTClient:
    def __init__(self, username, password, iface, tcpport) :
        self.iface = iface
        self.tcpport = tcpport
        self.username = username
        self.password = password
        self.salt = read_file('salt')
        self.client = noise_prot_interface.NoiseProtocolClient()


    def _connect(self, srcIP, dstIP):
        pkt = IP(src = srcIP, dst = dstIP)
        self.client.connect()
        mqtt = MQTTConnect(username = username, password = Credentials().hash_pwd(self.salt, self.password))
        self.client.sendMessage(mqtt)
        return self.client.getMessage()


    #def _subscribe():
    #def _publish()

def main():
    print("Args: %s" % (sys.argv))
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:t:u:p:d:",["interface=","tcpport=","username=","password=","dst="])
    except getopt.GetoptError:
        print ("%s -t <TCP port> -u <username> -p <password> -d <dst>" % (sys.argv[0]))
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("%s -t <TCP port> -u <username> -p <password> -d <dst>" % (sys.argv[0]))
            sys.exit()
        elif opt in ("-t", "--tcpport"):
            tcpport = int(arg)
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-d", "--dst"):
            dst = arg

    s_ip = 'localhost' 
    client = MQTTClient('', tcpport, username, password)
    print(client._connect(s_ip, dst))

main()
