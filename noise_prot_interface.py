import socket
from itertools import cycle

from noise.connection import NoiseConnection
'''
Class that implements the server of a connection.
It has 2 methods:
	sendMessage: sends a string to the server
		By default it listens to al interfaces and in port 2000.
		Just call '.listen()'
	getMessage: return a string recevied. It blocks the program until a message is received
		By default connects to localhost port 2000.
		To connect to a different machine use: ' connect('192.168.1.22',2000)' or similar

'''
class NoiseProtocolServer:
    def listen(self,interface='',port=2000):
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((interface, port))
        self.s.listen(1)
        self.conn, addr = self.s.accept()
        print('Accepted connection from', addr)
        self.noise = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
        self.noise.set_as_responder()
        self.noise.start_handshake()
        # Perform handshake. Break when finished
        for action in cycle(['receive', 'send']):
            if self.noise.handshake_finished:
                break
            elif action == 'send':
                ciphertext = self.noise.write_message()
                self.conn.sendall(ciphertext)
            elif action == 'receive':
                data = self.conn.recv(2048)
                plaintext = self.noise.read_message(data)

    def sendMessage(self,message):
        message_str= str(message)
        self.conn.sendall(self.noise.encrypt(message_str.encode('utf-8')))
    
    def getMessage(self):
        data = self.conn.recv(2048)
        if not data:
            return ''
        return self.noise.decrypt(data).decode("utf-8")
'''
Class that implements the client part of a connection.
It has 2 methods:
	(the methods do the same as in the server))
	sendMessage: sends a string to the server
	getMessage: return a string recevied. It blocks the program until a message is received
'''
class NoiseProtocolClient:
    def connect(self,destination='localhost',port=2000):
        self.sock = socket.socket()
        self.sock.connect((destination, port))
        # Create instance of NoiseConnection, set up to use NN handshake pattern, Curve25519 for
        # elliptic curve keypair, ChaCha20Poly1305 as cipher function and SHA256 for hashing.
        self.proto = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
        # Set role in this connection as initiator
        self.proto.set_as_initiator()
        # Enter handshake mode
        self.proto.start_handshake()
        # Perform handshake - as we are the initiator, we need to generate first message.
        # We don't provide any payload (although we could, but it would be cleartext for this pattern).
        message = self.proto.write_message()
        # Send the message to the responder - you may simply use sockets or any other way
        # to exchange bytes between communicating parties.
        self.sock.sendall(message)
        # Receive the message from the responder
        received = self.sock.recv(2048)
        # Feed the received message into noise
        payload = self.proto.read_message(received)
        # As of now, the handshake should be finished (as we are using NN pattern).
        # Any further calls to write_message or read_message would raise NoiseHandshakeError exception.
        # We can use encrypt/decrypt methods of NoiseConnection now for encryption and decryption of messages.
        return 0
    def sendMessage(self,message):
        message_str= str(message)
        self.sock.sendall(self.proto.encrypt(message_str.encode('utf-8')))
    
    def getMessage(self):
        data = self.sock.recv(2048)
        if not data:
            return ''
        return self.proto.decrypt(data).decode("utf-8")
