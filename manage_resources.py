import sys
import docker
import threading
import tarfile
import os
import getopt

class Infrastructure():

    def __init__(self):
        self.docker_client = docker.from_env()
        self.container_prefix_name = 'container_'
        self.docker_image = 'python:2.7.15-alpine3.8'
        self.network_name = 'myfarm'


    def add_resource(self, id, resource):

        print 'Add resource: IN PROGRESS'

        target_container_name = self.container_prefix_name + id
        containers = self.docker_client.containers.list()
        target_container = None

        for container in containers:
            if (container.name == target_container_name):
                target_container = container
                break

        if (target_container):    
            (exit_code, output) = container.exec_run(workdir='/CoAPthon', cmd='python manage_resources_sock.py -o a  -r' + ' ' + resource)
            print output
        else:
            print '    container not found'

        print 'Add resource: DONE'

    def del_resource(self, id, resource):
    
        print 'Del resource: IN PROGRESS'

        target_container_name = self.container_prefix_name + id
        containers = self.docker_client.containers.list()
        target_container = None

        for container in containers:
            if (container.name == target_container_name):
                target_container = container
                break

        if (target_container):    
            (exit_code, output) = container.exec_run(workdir='/CoAPthon', cmd='python manage_resources_sock.py -o d  -r' + ' ' + resource)
            print output
        else:
            print '    container not found'

        print 'Del resource: DONE'

    def list_resources(self, id):

        print 'List resource: IN PROGRESS'

        target_container_name = self.container_prefix_name + id
        containers = self.docker_client.containers.list()
        target_container = None

        for container in containers:
            if (container.name == target_container_name):
                target_container = container
                break

        if (target_container):
            (exit_code, output) = container.exec_run(workdir='/CoAPthon', cmd='python manage_resources_sock.py -o l')
            print output
        else:
            print '    container not found'

        print 'List resource: DONE'

if __name__ == '__main__':

    infrastructure = Infrastructure()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:i:r:', ['operation=', 'id=', 'resource='])

        operation = None
        resource = None
        id = None

        for o, arg in opts:

            # id, resource_name
            if o in ('-o', '--operation'):
                operation = arg

            elif o in ('-i', '--id'):
                id = arg

            elif o in ('-r', '--resource'):
                resource = arg

        if (operation == 'l' and id):
            infrastructure.list_resources(id)

        elif (operation == 'a' and id and resource):
            infrastructure.add_resource(id, resource)

        elif (operation == 'd' and id and resource):
            infrastructure.del_resource(id, resource)
        else:
            raise ValueError('manage_resources: Missing params')

    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)