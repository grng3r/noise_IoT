#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

import noise_prot_interface
from scapy.contrib.mqtt import *
from scapy.all import *
from mqtt_broker import Credentials
import socket
import sys, getopt

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


    def syn_ack(self, srcIP, dstIP):
        #syn
        ip = IP(src = srcIP, dst = dstIP)
        syn = TCP(sport = self.tcpport, dport = self.tcpport, flags = 's', seq = 1000)
        self.client.sendMessage(syn)
        syn_ack = self.client.getMessage()
        #ack
        ack = TCP(sport = self.tcpport, dport = self.tcpport, seq = syn_ack.ack, ack = syn_ack.seq + 1)
        self.client.sendMessage(ack)

    #def tcp_fin(self):

    def _connect(self):
        self.client.connect()
        mqtt = MQTT()/MQTTConnect(username = self.username.encode('utf-8'), password = Credentials().hash_pwd(bytes(self.salt, encoding='utf-8'), bytes(self.password, encoding='utf-8')))
        print("connect packet {}".format(mqtt))
        self.client.sendMessage(raw(mqtt))
        return self.client.getMessage()


    def _subscribe(self, topics = []):
        self.client.connect()
        mqtt = MQTT(QOS=2)/MQTTSubscribe(topics = topics)
        print("subscribe packet {}".format(raw(mqtt)))
        self.client.sendMessage(raw(mqtt))
        return self.client.getMessage()


    def _publish(self, topic, value):
        mqtt = MQTT()/MQTTPublish(topic = topic, value = value)
        self.client.sendMessage(mqtt)
        return self.client.getMessage()

    def _ping(self):
        mqtt = MQTT(type = 12)
        self.client.sendMessage(mqtt)
        return self.client.getMessage()

    def _disconnect(self):
        mqtt = MQTT()/MQTTDisconnect()
        self.client.sendMessage(mqtt)
        return self.client.getMessage()


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
        #TODO topic arg
        #TODO pub sub arg
    #print(password)
    s_ip = 'localhost' 
    client = MQTTClient(username, password, '', tcpport)
    print(client._connect())
    print(client._subscribe(['topic']))

main()
