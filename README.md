# Noise IoT Project

## Authors
 - Jaime Galán Martínez
 - Mario Vuksa
 - Víctor Aranda López

## Noise protocol summary

Noise is a protocol framework for 2 party secure-channel protocols. It provides a simple pattern
language and naming scheme for 2-party DH-based cryptographic handshakes, covering the different
possibilities for client and/or server authentication, post/pre-specified peers, identity-hiding
and 0-RTT encryption. These patterns are easily compiled into linear sequences of cryptographic
operations using your favorite ECDH, hash, and cipher functions.

Used by Wireguard and WhatsAPP
## Crypto Background

### Authenticated key exchange - AKE

Sequence of messages exchanged by 2 parties to authenticate each other and establish a shared
secret key.
Properties:
    - forward secrecy
    - mutual or 1-way authentication
    - pre-knowledge of identities, identity-hiding
    - crypto used: DH, certs, signatures

## Secure Channel Protocol

All have same structure:
- Handshake phase: Authenticates and establishes shared secret
    - Negotiation (determines type of AKE, parameters of AKE, type of encryption) -> can have fallback options
    - AKE
- Transport phase: Uses shared secret keys to ecrypt data

## Noise Framework

Designed to build a protocol for a specific use case, so you want to think in advance which AKE
to use and which cryptography to get, to remove complexity. This is very unlike TLS  for example
where the negotiation happens over which cryptography and key exchange is accepted. This because
we want to remove branching, improve testability through:
- runtime decisions are made only when we select the noise protocol
- this selection encupsulates everything in a linear sequence of code(AKE+transport encryption)

Noise protocol brakedown:
- Negotiation layer - 1 transition, if first selection fails go to other, no more than 2 posibilities
- Handshake Pattern(abstract AKE) instantiated by:
    - Public key crypto
    - Symmetric crypto
- Encoding layer: ex. sending over TCP so add length fields, HTTP encoding etc.

Noise protocol are defined by their names. 


# Python modules

## Noise Protocol Framework - Python 3 implementation
We used the following Noise Protocol implementation for our project: https://github.com/plizonczyk/noiseprotocol

## noise_prot_interface.py
Python file that has two main classes: NoiseProtocolServer and NoiseProtocolCLient.

## mqtt_broker2.py

Opens socket and waits for connection from client, when client connects sends message.

## mqtt_cli2.py

When establishes connection to server receives message. It publishes messages about the CPU's temperature to the server.


The communication can be observed on any platform with Wireshark looking at the loopback interface.

## Setup

Create python virtual environment with (depending on your system you might have to change python3 to python and pip3 to pip):
```
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
```

Run server in one terminal and the client in the other. For doing that run the following scripts:
- ./run_broker.sh   (python3 mqtt_broker2.py -u iot -p iot)
- ./run_cli.sh      (python3 mqtt_cli2.py -u iot -p iot -t cpu_temp -c pub -n 2000)

## Read/Watch list

- [1] https://www.youtube.com/watch?v=C-kWVb81tCc
- [2] https://noiseprotocol.org/noise.html
- [3] https://noiseprotocol.org/specs/noisesocket.html
