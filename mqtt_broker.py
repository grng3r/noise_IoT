#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

from scapy.all import *
from threading import Thread, Lock, Timer
from scapy.contrib.mqtt import *
import random
import sys#, getopt
#import pdb
from noise_prot_interface import *

# Dictionary of subscribers: each entry has the topic as key and a list of lists ({IP address, TCP port, QoS}) of the subscribers for that topic
subscribersForTopic = {}
subscribersForTopic_lock = Lock() # To avoid concurrent access
# Dictionary of TCP connections (key = tuple([IP address, TCP port]) (IP address and TCP port from destination), value = seq or ack (from the MQTT broker point of view))
tcpSeqList = {}
tcpAckList = {}

# TCP flags
FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80


#TODO functions to get credentials from encrypted data in simple file
class MQTTBroker:
    def __init__(self, iface, tcpport, username, password):
        self.iface = iface
        self.tcpport = tcpport
        self.username = username
        self.password = password
        self._timeout = 1
        self._noClients = 0


    def _ack_p(self, p):
        i = tuple([p[IP].src,p[TCP].sport])

        ip = IP(src=p[IP].dst, dst=p[IP].src)
        ackPacket = ip/TCP(sport=self.tcpport, dport=p[TCP].sport, flags='A', seq=tcpSeqList[i], ack=tcpAckList[i])
        return ackPacket


     def _disconnect(self, dstIPAddress, srcIPAddress, tcpPort, connected):
        connected = False

        # Check if this IP address and TCP port is a subscriber, and remove from the list
        with subscribersForTopic_lock:
            for topic in subscribersForTopic.copy():
                subscribersList = subscribersForTopic[topic]
                subscribersList = [x for x in subscribersList if not(x[0] == srcIPAddress and x[1] == tcpPort)] # Removing based on the content of the first element.
                                                                                                              # Maybe list comprehension is not the best for performance, but it works...
                subscribersForTopic[topic] = subscribersList                                                    # Required since subscribersList is now a different object
                # If this key has no content, remove it from the dictionary
                if not subscribersForTopic[topic]:
                    del subscribersForTopic[topic]

        print("[%s] %s (TCP port %d) disconnected. TOPICS-SUBSCRIBERS list:         %s" % (threading.currentThread().getName(), srcIPAddress, tcpPort, subscribersForTopic))


    def _timerExpiration(self, p, connected):
        print("[%s] Keep alive (MQTT PING REQUEST) timeout!!!" % (threading.currentThread().getName()))
        self._disconnect(p[IP].dst, p[IP].src, p[TCP].sport, connected)


    def _ack_rclose_p(self, p, connected):
        # Finish connection
        connected = False

        # The following line is commented to avoid forwarding two DISCONNECT REQ message when e.g. PUBLISHing a message
        # (the first one due to the DISCONNECT REQ, the second one due to the TCP FIN packet)
        # In the case of closing with ctrl+C a subscriber, the DISCONNECT REQ message will be forwarded when
        # the corresponding timer (for PING REQ) expires.

        self._disconnect(p[IP].dst, p[IP].src, p[TCP].sport, connected)

        # Send FIN + ACK
        i = tuple([p[IP].src,p[TCP].sport])

        ip = IP(src=p[IP].dst, dst=p[IP].src)
        finAckPacket = ip/TCP(sport=self.tcpport, dport=p[TCP].sport, flags='FA', seq=tcpSeqList[index], ack=tcpAckList[index])
        tcpSeqList[index] = tcpSeqList[index] + 1
        return finAckPacket


    def mqtt_broker(self, p):
        connected = True
        keepalive = 60
        t_name = threading.currentThread().getName()
        server = NoiseProtocolServer()
        print("[%s] NEW THREAD for client %s (TCP port %s)" % (threadName, clientIPAddress, clientTCPPort))
        while connected:
            # MQTT mssg
            if p.haslayer(TCP) and p.haslayer(MQTT) and p[TCP].dport = self.tcpport:
                i = tuple(p[IP].src, p[TCP].sport)
                print("[%s] %s MQTT packet type: %d" % (threadName, i, p[MQTT].type))
                print("[%s] tcpAckList: %s" % (threadName, tcpAckList))
                tcpAckList[index] = tcpAckList[index] + len(p[MQTT])

                # Send ACK
                if not p[TCP].flags & 0x01 == 0x01:
                    # Normal ACK
                    ack = self._ack_p(p)
                    server.sendMessage(ack)
                else:
                    # FIN received, sending FIN+ACK (this happens with the MQTT DISCONNECT message, which does not require an MQTT response)
                    connected = False
                    print("[%s] tcpAckList: %s" % (threadName, tcpAckList))
                    tcpAckList[index] = tcpAckList[index] + 1
                    fin_ack = self._ack_rclose(p, connected)
                    server.sendMessage(fin_ack)
                    #TODO process mssg type
            # TCP FIN received, sending TCP FIN+ACK
            elif p.haslayer(TCP) and p[TCP].dport == self.tcpport and p[TCP].flags & FIN:
                i = tuple([p[IP].src,p[TCP].sport])
                print ("[%s] %s TCP FIN received" % (threadName, i))

                connected = False
                print("[%s] tcpAckList: %s" % (threadName, tcpAckList))
                tcpAckList[index] = tcpAckList[i] + 1
                self._ack_rclose(p, connected)

            # TCP ACK received
            elif p.haslayer(TCP) and p[TCP].dport == self.tcpport and p[TCP].flags & ACK:
                i = tuple([p[IP].src,p[TCP].sport])
                print ("[%s] %s TCP ACK received!" % (threadName, i)) # Do nothing

        self._mqttServerThread = None
        print('[%s] MQTT server thread stopped' % (threadName))


