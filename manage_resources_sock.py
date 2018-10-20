import select
import socket
import struct
import threading
import time
import getopt
import sys


class Client():

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.local_address = (socket.gethostbyname(socket.gethostname()), 5000)

    def senddata(self, data, address):
        sent = self.sock.sendto(data, address)
        if sent == 0:
            raise RuntimeError('socket connection broken')

        self.recvdata()

    def recvdata(self):
        datagram = ''

        try:
            while True:
                datagram, address = self.sock.recvfrom(1024)
                if address == '':
                    raise RuntimeError('socket connection broken')

                print datagram
                return datagram

        except socket.timeout as error:
            print 'timeout'
            print error.message

        except Exception as error:
            self.sock.close()

if __name__ == "__main__":

    client = Client()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:r:', ['operation=', 'resource='])
        operation = None
        resource = None

        for o, arg in opts:
            if o in ('-o', '--operation'):
                operation = arg
            elif o in ('-r', '--resource'):
                resource = arg

        if (operation == 'l' or operation == 'a' or operation == 'd'):
            if resource != None:
                operation = operation + ' ' + resource
            client.senddata(operation, client.local_address)
        else:
            raise ValueError('manage_resources_sock: Missing params')

    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)
