#!/home/grng3r/Desktop/faks_upm/Security_IoT/proj/venv/bin/python3
# -*- coding: utf-8 -*-

from scapy.all import *
from threading import Thread, Lock, Timer
from scapy.contrib.mqtt import *
import random
import sys, getopt
import noise_prot_interface

import secrets
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
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


    def _broadcast_topic_mssg(self, p, topic, mssg):
        with subscribersForTopic_lock:
            if topic in subscribersForTopic:
                subscribersList = subscribersForTopic[topic]
                for x in subscribersList:
                    ipAdd = x[0]
                    tcpPort = x[1]
                    QOS = x[2]
                    print("Broadcasting MQTT PUBLISH - sending message %s to %s (TCP port %d) with topic %s and QoS %d" % (message, ipAddress, tcpPort, topic, QOS))

                    i = tuple([ipAdd, tcpPort])
                    ipB = IP(src = p[IP].dst, dst = ipAdd)
                    tcpB = TCP(sport = self.tcpport, dport = tcpPort, flags = 'A', seq = tcpSeqList[i], ack = tcpAckList[i])
                    mqttB = MQTT()/MQTTPublish(topic = topic, value = mssg)
                    server.sendMessage(ipB/tcpB/mqttB)
                    tcpSeqList[i] = tcpSeqList[i] + len(mqttB)
            else:
                print("Broadcasting MQTT PUBLISH - no one subscribed to topic %s" % (topic))


    def mqtt_broker(self, server, clientIPAddress, clientTCPPort):
        connected = True
        keep_alive = 60
        t_name = threading.currentThread().getName()
        print("[%s] NEW THREAD for client %s (TCP port %s)" % (threadName, clientIPAddress, clientTCPPort))
        while connected:
            p = server.getMessage()
            if p == None:
                print("Connected")
            else:
                # MQTT mssg
                if p.haslayer(TCP) and p.haslayer(MQTT) and p[TCP].dport == self.tcpport:
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

                    if p[MQTT].type == 1:
                        #MQTT CONNECT received, sending MQTT CONNACK
                        keep_alive = p[MQTT].klive
                        ip = IP(src = p[IP].dst, dst = p[IP].src)
                        tcp = TCP(sport = self.tcpport, dport = p[TCP].sport, flags = 'A', seq = tcpSeqList[i], ack = tcpAckList[i])
                        if p[MQTT].username.decode('utf-8') == self.username and p[MQTT].password.decode('utf-8') == self.password:
                            mqtt = MQTT()/MQTTConnack(sessPresentFlag = 1, retcode = 5)
                            print("[%s] %s MQTT CONNECT received, wrong user/password" % (threadName, i))
                        server.sendMessage(ip/tcp/mqtt)
                        tcpSeqList[i] = tcpSeqList[i] + len(mqtt)

                    elif p[MQTT].type == 3:
                        # MQTT PUBLISH received
                        topic = p[MQTT][1].topic
                        message = p[MQTT][1].value
                        print("[%s] %s MQTT PUBLISH received, topic=%s, message=%s" % (threadName, i, topic, message))
                        #Broadcast MQTT PUBLISH to subscriber connected to the server
                        self._broadcast_topic_mssg(p, topic.decode('utf-8'), message.decode('utf-8'))

                    elif p[MQTT].type == 8:
                        # MQTT SUBSCRIBE received, sending MQTT SUBACK
                        topic = p[MQTT][2].topic
                        QOS = p[MQTT][2].QOS
                        ipAdd = p[IP].src
                        tcpPort = p[TCP].sport
                        print("[%s] %s MQTT SUBSCRIBE received, topic=%s, QoS=%d" % (threadName, index, topic, QOS))

                        # add subscribers to topics
                        with subscribersForTopic_lock:
                            if topic.decode('utf-8') in subscribersForTopic:
                                subscribersForTopic = subscribersForTopic[topic.decode('utf-8')]
                                subscribersForTopic.append([ipAdd, tcpPort, QOS])
                            else:
                                subscribersForTopic[topic.decode('utf-8')] = [[ipAdd, tcpPort, QOS]]
                        print("[%s] %s Subscribers list for this topic: %s" % (threadName, index, subscribersForTopic[topic.decode('utf-8')]))
                        print("[%s] %s TOPICS-SUBSCRIBERS list:         %s" % (threadName, index, subscribersForTopic))

                        ip = IP(src = p[IP].dst, dst = p[IP].src)
                        tcp = TCP(sport = self.tcpport, dport = p[TCP].sport, flags = 'A', seq = tcpSeqList[i], ack = tcpAckList[i])
                        mqtt = MQTT()/MQTTSuback(msgid = p[MQTT].msgid, retcode = QOS)
                        tcpSeqList[i] = tcpSeqList[i] + len(mqtt)

                        # Create a timer. If there is a timeout (PING REQUEST not received), the client is assumed to be disconnected.
                        print("[%s] %s KEEP ALIVE timer started!!!" % (threadName, index))
                        t = Timer(keepAlive+10, self._timerExpiration, args=(p, connected,))
                        t.start()

                    elif p[MQTT].type == 12:
                        #PING request received, sending MQTT PING response
                        ip = IP(src = p[IP].dst, dst = p[IP].src)
                        tcp = TCP(sport = self.tcpport, dport = p[TCP].sport, flags = 'A', seq = tcpSeqList[i], ack = tcpAckList[i])
                        mqtt = MQTT(type = 13, len = 0)
                        server.sendMessage(ip/tcp/mqtt)
                        tcpSeqList[i] = tcpSeqList[i] + len(mqtt)

                        # restart timer
                        print("[%s] %s Keep alive timer restarted!!!" % (threadName, index))
                        t.cancel()
                        t = Timer(keepAlive+10, self._timerExpiration, args=(p, connected,))
                        t.start()

                    elif p[MQTT].type == 14:
                        print("[%s] %s MQTT DISCONNECT REQ received" % (threadName, index))
                        self._disconnect(p[IP].dst, p[IP].src, p[TCP].sport, connected)
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


    def _start_mqttServerForThisClientThread(self, clientIPAddress, clientTCPPort, server):
        self._noClients = self._noClients + 1
        print("[MAIN] STARTING THREAD for serving MQTT client no. %s (name=%s) ..." % (str(self._noClients), threading.currentThread().getName()))
        mqttServerForThisClientThread = Thread(name='MQTTServerThread'+str(self._noClients), target=self._mqttBroker, args=(server, clientIPAddress, clientTCPPort))
        mqttServerForThisClientThread.start()

    def listen(self):
        server = noise_prot_interface.NoiseProtocolServer() 
        while True:
            print("[MAIN] Waiting for a new connection on port " + str(self.tcpport) + "...")
            # wait for a new connections 
            try:
                print("[MAIN] Waiting for a new connection on port " + str(self.tcpport) + "...")
                # Wait for a new connection
                synPacket = server.listen(self.iface, self.tcpport)
                print(synPacket)
                if synPacket != '':
                    print ("[MAIN] NEW CONNECTION: Received TCP SYN from %s (TCP port %s)" % (synPacket[IP].src, synPacket[TCP].sport))
                    # Create TCP SYN+ACK packet
                    #sport = synPacket[TCP].sport
                    #index = tuple([synPacket[IP].src,synPacket[TCP].sport])
                    #tcpSeqList[index] = random.getrandbits(32) # Random number of 32 bits
                    #tcpAckList[index] = synPacket[TCP].seq + 1 # SYN+ACK
                    print("[MAIN] tcpAckList: %s" % (tcpAckList))

                    # Generating the IP layer
                    #ip = IP(src=synPacket[IP].dst, dst=synPacket[IP].src)
                    # Generating the TCP layer
                    #tcpSynAck = TCP(sport=self.tcpport, dport=sport, flags="SA", seq=tcpSeqList[index], ack=tcpAckList[index], options=[('MSS', 1460)])
                    # Start new thread for this connection
                    self._start_mqttServerForThisClientThread(synPacket[IP].src, synPacket[TCP].sport)
                    # Send SYN+ACK and receive ACK
                    tcpSeqList[index] = tcpSeqList[index] + 1
                    server.sendMessage(ip/tcpSynAck)
            except Exception as e:
                #if socket or Noise error simply drop -> TODO might need to be processed differently
                print(e)
                pass

def save_to_file(data, f_name):
        with open(f_name, 'w') as f:
            f.write(data)


class Credentials():
    def __init__(self):
        self.users = {}

    def create_salt(self, bits):
        # secrets provides a cryptographicaly secure random number generator
        salt = secrets.token_bytes(bits)
        save_to_file(str(salt), 'salt')
        return salt

    def hash_pwd(self, salt, pwd):
        # key derivation function "safe" from HW attacks
        kdf = Scrypt(salt = salt, length = 32, n = 2**14, r = 8, p = 1)
        return kdf.derive(pwd)

    def store(self, salt, username, pwd):
        key = self.hash_pwd(salt, pwd)
        self.users[username] = key
        return self.users

    
def main():
    print("Args: %s" % (sys.argv))
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:t:u:p:",["interface=","tcpport=","username=","password="])
    except getopt.GetoptError:
        print ("%s -t <TCP port> -u <username> -p <password>" % (sys.argv[0]))
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("%s -t <TCP port> -u <username> -p <password>" % (sys.argv[0]))
            sys.exit()
        elif opt in ("-t", "--tcpport"):
            tcpport = int(arg)
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg

    #print("Listening MQTT on interface %s (TCP port %d)" % (interface, tcpport))
    server = noise_prot_interface.NoiseProtocolServer()
    print(server.listen())
            
    #salt = Credentials().create_salt(32)

    #users = Credentials().store(salt, username, str.encode(password))
    #for u,p in users.items():
        #print(u)
        #print(p)
        #broker = MQTTBroker('', tcpport, u, p)
        #broker.listen()


if __name__ == "__main__":
    main()
