import socket
import threading
import re
from queue import Queue

class ClientObj:
    def __init__(self, client, name, address):
        self.client = client
        self.name = name
        self.address = address


def SendMessageToSingle(message, client):
    client.send(message.encode())


class ChatServer:
    def __init__(self):
        self.host = ''
        self.port = 1337
        self.ServerSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

        self.commands = [
            {
                "regex": "setname",
                "method": self.RenameClient,
                "description": "Change your name into anything you want",
                "usage" : "\\setname [new_name]"
            },
            {
                "regex": "pm",
                "method": self.SendPrivateMessage,
                "description": "Send private message",
                "usage" : "\\pm [receiver_name] [message]"
            }]

    def SendMessageToAll(self, message, sender):
        for client_obj in self.clients:
            name = ""
            if client_obj.client == sender:
                name = client_obj.name
                break

        for client_obj in self.clients:
            if client_obj.client != sender:
                SendMessageToSingle("{}: {}".format(name, message), client_obj.client)

    def MakeAnnouncement(self, message):
        print(message)
        for client_obj in self.clients:
            SendMessageToSingle("Server: {}".format(message), client_obj.client)

    def WaitForMessage(self, this_client):
        while True:
            try:
                res = this_client.client.recv(1024)
            except ConnectionResetError:
                for client_obj in self.clients:
                    if client_obj.client == this_client.client:
                        self.clients.remove(client_obj)
                        self.MakeAnnouncement("{} has exited".format(client_obj.name))
                        break
                return


            message = res.decode('utf-8')
            print("test")
            print(message)

            if message[0] == '\\':
                parser_thread = threading.Thread(target=self.ParseCommands, args=(message[1:], this_client), group=None)
                parser_thread.start()
            else:
                sender_thread = threading.Thread(target=self.SendMessageToAll, args=(message, this_client.client), group=None)
                sender_thread.start()

    def WaitForNewClient(self):
        while True:
            client, address = self.ServerSideSocket.accept()

            queue = Queue()
            welcomer_thread = threading.Thread(target=self.WelcomeClient, args=(client, address, queue), group=None)
            welcomer_thread.start()
            welcomer_thread.join()
            client_obj = queue.get()

            message_listener_thread = threading.Thread(target=self.WaitForMessage, args=(client_obj,), group=None)
            message_listener_thread.start()

    def WelcomeClient(self, client, address, queue):
        client_obj = ClientObj(client=client, address=address, name=address[0] + ':' + str(address[1]))
        self.clients.append(client_obj)
        queue.put(client_obj)
        message = "Welcome {} to our beautiful server" \
                  "Available commands:".format(client_obj.name)
        for command in self.commands:
            message += ("\n{}\t{}".format("\\" + (command["regex"]), command["description"]))

        message += "\nACTIVE USERS:"
        for other_client_obj in self.clients:
            message += '\n' + other_client_obj.name

        SendMessageToSingle(message, client)

        self.MakeAnnouncement('{} connected'.format(client_obj.name))


    def StartServer(self):
        try:
            self.ServerSideSocket.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))

        print('Server socket is listening at {}'.format(self.port))
        self.ServerSideSocket.listen()

        welcoming_thread = threading.Thread(target=self.WaitForNewClient, group=None)  # as vgalo to group

        welcoming_thread.start()

    def RenameClient(self, name, this_client):
        for client_obj in self.clients:
            if client_obj.client == this_client.client:
                announcement = "{} has changed their name into \"{}\"".format(client_obj.name, name)
                self.MakeAnnouncement(announcement)
                client_obj.name = name
                return

    def SendPrivateMessage(self, data, this_client):
        data = data.split(' ', 1)
        if len(data) < 2:
            SendMessageToSingle("WRONG USAGE", this_client.client)
            return
        name = data[0]
        message = data[1]
        message = "PM FROM {}: {}".format(this_client.name, message)
        for client_obj in self.clients:
            if client_obj.name == name:
                SendMessageToSingle(message, client_obj.client)
                return
        SendMessageToSingle("USER {} NOT FOUND".format(name), client_obj.client)

    def ParseCommands(self, command, client_obj):
        for command_dic in self.commands:
            parsed_command = re.split('^{} '.format(command_dic['regex']), command)
            if len(parsed_command) > 1:
                command_dic['method'].__call__(parsed_command[1], client_obj)
                return


server = ChatServer()
server.StartServer()
