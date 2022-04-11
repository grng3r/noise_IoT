#import socket
import noise_prot_interface
#from noise.connection import NoiseConnection
'''
Example of use of the client of noise protocol.
It connects to a server ( by default it is in localhost, port 2000)
and reads the standard input, then it sends that string to the serverin a secured way.
Finally, it prints the message received by the server.
'''
client = noise_prot_interface.NoiseProtocolClient()
client.connect()

while True:
    text =input()
    client.sendMessage(text)
    msg=client.getMessage()
    print(msg)