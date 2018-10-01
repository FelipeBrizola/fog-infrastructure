import select
import socket
import struct
import threading
import time
import getopt
import sys

class Client():

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.bind(('', 0))
        self.readers = []
        self.writers = []
        self.rbuff = ''
        self.wbuff = ''
        self.reader_callback = None
        self.quit = False

    def _senddata(self, writer):
        sentcount = 0
        bufferlen = len(self.wbuff)
        while sentcount < bufferlen:
            sent = self.client.sendto(
                self.wbuff[sentcount:], ('127.0.0.1', 5000))
            if sent == 0:
                raise RuntimeError("socket connection broken")
            sentcount += sent
            if sentcount == bufferlen:
                self.wbuff = ''
                self.writers.remove(writer)

    def _recvdata(self):
        data = ''

        try:
            while True:
                chunk = self.client.recvfrom(1024)
                if chunk == '':
                    raise RuntimeError("socket connection broken")

                data = data + chunk[0]
        except:
            pass
        finally:
            if not self.reader_callback == None:
                self.reader_callback(data)

    def cycle(self):
        try:
            self._stop = False
            self.client.settimeout(1)
            while self._stop == False:
                rlist, wlist, xlist = select.select(
                    self.readers, self.writers, [], 1)
                for reader in rlist:
                    self._recvdata()
                for writer in wlist:
                    self._senddata(writer)

        except Exception as e:
            print "An error occurred in Client.cycle()\n" + str(e)

    def close(self):
        try:
            self.client.close()
            self._stop = True
        except Exception as e:
            print("An error occurred in Listener.close():\n" + str(e))


def callback(message):
    print(message)


if __name__ == "__main__":

    # Create client and listen for incoming responses
    client = Client()
    client.readers.append(client.client)
    client.reader_callback = callback
    listener_thread = threading.Thread(target=client.cycle)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:i:r:', ['operation=', 'id=', 'resource='])

        operation = None
        resource = None
        id = None

        for o, arg in opts:

            if o in ('-o', '--operation'):
                operation = arg

            elif o in ('-r', '--resource'):
                resource = arg

        if (operation == 'l'):
            client.wbuff = 'l'
            client.writers.append(client.client)
            listener_thread.start()

        elif (operation == 'a' and resource):
            client.wbuff = 'a ' + resource
            client.writers.append(client.client)
            listener_thread.start()

        elif (operation == 'd' and resource):
            client.wbuff = 'd ' + resource
            client.writers.append(client.client)
            listener_thread.start()

        else:
            raise ValueError('manage_resources_sock: Missing params')

    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    # Wait for a timeout period (in case of slow resp) before closing
    time.sleep(10)
    client.close()
