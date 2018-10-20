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

    def remove_containers(self, containers):

        print 'Remove all containers: IN PROGRESS'

        threads_to_stop = []
        threads_to_remove = []

        # threads to stop containers
        for container in containers:
            thread = threading.Thread(target=container.stop, name=container.name)
            threads_to_stop.append(thread)
            print '    Start thread to stop ' + str(thread.name)
            thread.start()
        for thread in threads_to_stop:
            thread.join()

        # threads to remove containers
        for container in containers:
            thread = threading.Thread(target=container.remove, name=container.name)
            threads_to_remove.append(thread)
            print '    Start thead to remove ' + str(thread.name)
            thread.start()
        for thread in threads_to_remove:
            thread.join()

        print 'Remove all containers: DONE'


    def make_tarfile(self, output_filename, source_dir):
        with tarfile.open(output_filename, 'w:gz') as tar:
            tar.add(source_dir, recursive=True, exclude=None, arcname=os.path.basename(source_dir))


    def deploy_containers(self, docker_image, network_name, container_prefix_name, containers_quantity, container_id=None):

        print 'Deploy containers: IN PROGRESS'

        containers = []

        for index in range(0, containers_quantity):
            if container_id:
                name = container_prefix_name + str(container_id)
            else:
                name = container_prefix_name + str(index)

            # $ docker run -i -t python:2.7.15-alpine3.8 /bin/sh
            containers.append(self.docker_client.containers.run(image=docker_image, command='/bin/sh',
                                                        tty=True, stdin_open=True, network=network_name, detach=True, name=name))
            print '    ' + name + ' is running!'

        print 'Deploy containers: DONE'

        return containers


    def push_project(self, containers):

        print 'Send project folder to containers: IN PROGRESS'

        # generate tar file
        self.make_tarfile('../CoAPthon.tar', '../CoAPthon')
        self.make_tarfile('../manage_resources_sock.tar', './manage_resources_sock.py')
        self.make_tarfile('../resource_mapping.tar', '../resource_mapping')
        self.make_tarfile('../coapclient.tar', '/usr/local/lib/python2.7/site-packages/coapthon')

        # put on containers
        for container in containers:
            project = open('../CoAPthon.tar', 'r')
            container.put_archive(path='/', data=project)
            project.close()

            project = open('../manage_resources_sock.tar', 'r')
            container.put_archive(path='/CoAPthon', data=project)
            project.close()

            project = open('../resource_mapping.tar', 'r')
            container.put_archive(path='/', data=project)
            project.close()

            project = open('../coapclient.tar', 'r')
            container.put_archive(path='/usr/local/lib/python2.7/site-packages', data=project)
            project.close()

            print '    sent to ' + container.name

        os.remove('../CoAPthon.tar')
        os.remove('../manage_resources_sock.tar')
        os.remove('../resource_mapping.tar')
        os.remove('../coapclient.tar')

        print 'Send project folder to containers: DONE'


    def create_network(self, network_name):

        print 'Create network: IN PROGRESS'

        ipam_pool = docker.types.IPAMPool(subnet='192.168.0.0/24')
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        self.docker_client.networks.create(
            name=network_name, driver='bridge', ipam=ipam_config)

        print 'Create network: DONE'


    def run_coap_servers(self, containers):

        print 'Run coap servers: IN PROGRESS'

        for container in containers:
            container.exec_run(workdir='/CoAPthon', cmd='python coapserver.py', detach=True)
            container.exec_run(workdir='/resource_mapping', cmd='python synchronizer.py', detach=True)
            print '    coap server is running on ' + container.name

        print 'Run coap servers: DONE'


    def next_container_id(self):

        list_ids = []
        containers = self.docker_client.containers.list()

        for container in containers:
            container_id = container.name.split('_')[1]
            list_ids.append(int(container_id))

        list_ids.sort()
        return len(list_ids)


    def add_container(self):

        print 'Add container: IN PROGRESS'

        container_id = self.next_container_id()
        containers_quantity = 1

        # run containers
        containers = self.deploy_containers(
            self.docker_image, self.network_name, self.container_prefix_name, containers_quantity, container_id)

        # put project on each container
        self.push_project(containers)

        # run coap server on each container
        self.run_coap_servers(containers)

        print 'Add container: DONE'


    def remove_container(self, container_id):

        print 'Remove container: IN PROGRESS'

        container_name = self.container_prefix_name + container_id

        print '    Removing ' + container_name
        try:
            container = self.docker_client.containers.get(container_name)
            container.stop()
            container.remove()
            print 'Remove container: DONE'

        except docker.errors.NotFound as err:
            print err.message
            print 'Remove container: ERROR'


    def purge(self):

        print 'Purge containers: IN PROGRESS'

        # Remove all container(stoped or not)
        containers = self.docker_client.containers.list()
        thread = threading.Thread(target=self.remove_containers, args=(containers,))
        thread.start()
        thread.join()

        # Remove stopped containers
        self.docker_client.containers.prune(filters=None)
        # Remove unused networks
        self.docker_client.networks.prune(filters=None)

        print 'Purge containers: DONE'


    def build_farm(self, containers_quantity):

        print 'Build farm: IN PROGRESS'

        self.purge()

        # create network
        self.create_network(self.network_name)

        # run containers
        containers = self.deploy_containers(
            self.docker_image, self.network_name, self.container_prefix_name, containers_quantity)

        # put project on each container
        self.push_project(containers)

        # run coap server on each container
        self.run_coap_servers(containers)

        print 'Build farm: DONE'


if __name__ == '__main__':

    infrastructure = Infrastructure()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ao:r:b:po', [
                                   'add', 'remove=', 'build=', 'purge'])

        # TODO: add or remove resource from container
        for o, arg in opts:
            if o in ('-a', '--add'):
                infrastructure.add_container()
            elif o in ('-r', '--remove'):
                infrastructure.remove_container(arg)
            elif o in ('-b', '--build'):
                infrastructure.build_farm(int(arg))
            elif o in ('-p', '--purge'):
                infrastructure.purge()

    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)
