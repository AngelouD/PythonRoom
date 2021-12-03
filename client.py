import socket
import threading


class ChatClient:

    def __init__(self):
        self.ClientSideSocket = socket.socket()
        self.host = 'localhost'
        self.port = 1337

    def SendMessage(self):
        while True:
            message = input("")
            self.ClientSideSocket.send(message.encode())

    def WaitForMessage(self):
        while True:
            res = self.ClientSideSocket.recv(1024)
            print(res.decode('utf-8'))

    def StartClient(self):
        try:
            self.ClientSideSocket.connect((self.host, self.port))
        except socket.error as e:
            print(str(e))

        message_sender_thread = threading.Thread(target=self.SendMessage)
        message_listener_thread = threading.Thread(target=self.WaitForMessage)

        message_listener_thread.start()
        message_sender_thread.start()

client = ChatClient()
client.StartClient()
