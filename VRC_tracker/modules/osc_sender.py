from pythonosc import udp_client

class OSCSender:
    def __init__(self, host, port):
        self.client = udp_client.SimpleUDPClient(host, port)

    def send(self, address, value):
        self.client.send_message(address, value)
