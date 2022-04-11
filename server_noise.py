#import socket
#from itertools import cycle
import noise_prot_interface
#from noise.connection import NoiseConnection
'''
Example of use of the server of noise protocol.
Accepts connections ( by default in port 2000).
When it connects with a client, it echo everything received.
Finally, it prints the message received by the client.
'''
server = noise_prot_interface.NoiseProtocolServer()
server.listen()

while True:
    msg=server.getMessage()
    print(msg)
    server.sendMessage(msg)