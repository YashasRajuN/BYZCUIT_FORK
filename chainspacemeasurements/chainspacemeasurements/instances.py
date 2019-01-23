"""EC2 instance management."""
import time
import os
import sys
from multiprocessing.dummy import Pool
import random
import math

import boto3
import paramiko


class ChainspaceNetwork(object):
    threads = 100
    aws_api_threads = 5

    def __init__(self, network_id, aws_region='us-east-2'):
        self.network_id = str(network_id)

        self.aws_region = aws_region
        self.ec2 = boto3.resource('ec2', region_name=aws_region)

        self.ssh_connections = {}
        self.shards = {}

        self.logging = True

    def _get_running_instances(self):
        return self.ec2.instances.filter(Filters=[
            {'Name': 'tag:type', 'Values': ['chainspace']},
            {'Name': 'tag:network_id', 'Values': [self.network_id]},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ])

    def _get_stopped_instances(self):
        return self.ec2.instances.filter(Filters=[
            {'Name': 'tag:type', 'Values': ['chainspace']},
            {'Name': 'tag:network_id', 'Values': [self.network_id]},
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ])

    def _get_all_instances(self):
        return self.ec2.instances.filter(Filters=[
            {'Name': 'tag:type', 'Values': ['chainspace']},
            {'Name': 'tag:network_id', 'Values': [self.network_id]},
        ])

    def _log(self, message):
        if self.logging:
            _safe_print(message)

    def _log_instance(self, instance, message):
        message = '[instance {}] {}'.format(instance.id, message)
        self._log(message)

    def _single_ssh_connect(self, instance):
        self._log_instance(instance, "Initiating SSH connection...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=instance.public_ip_address, username='admin')
        self.ssh_connections[instance] = client
        self._log_instance(instance, "Initiated SSH connection.")

    def _single_ssh_exec(self, instance, command):
        self._log_instance(instance, "Executing command: {}".format(command))
        client = self.ssh_connections[instance]
        stdin, stdout, stderr = client.exec_command(command)
        output = ''
        for message in iter(stdout.readline, ''):
            output += message
            try:
                self._log_instance(instance, message.rstrip())
            except Exception:
                pass
        for message in stderr.readlines():
            try:
                self._log_instance(instance, message.rstrip())
            except Exception:
                pass
        self._log_instance(instance, "Executed command: {}".format(command))

        return (instance, output)

    def _single_ssh_close(self, instance):
        self._log_instance(instance, "Closing SSH connection...")
        client = self.ssh_connections[instance]
        client.close()
        self._log_instance(instance, "Closed SSH connection.")

    def _config_shards_command(self, directory):
        command = ''
        command += 'cd {0};'.format(directory)
        command += 'printf "" > shardConfig.txt;'
        for i, instances in enumerate(self.shards.values()):
            command += 'printf "{0} {1}/shards/s{0}\n" >> shardConfig.txt;'.format(i, directory)
            command += 'cp -r shards/config0 shards/s{0};'.format(i)

            # config hosts.config
            command += 'printf "" > shards/s{0}/hosts.config;'.format(i)
            for j, instance in enumerate(instances):
                command += 'printf "{1} {2} 3001\n" >> shards/s{0}/hosts.config;'.format(i, j, instance.private_ip_address)

            # config system.config
            initial_view = ','.join((str(x) for x in range(len(instances))))
            faulty_replicas = (len(instances)-1)/3
            faulty_replicas = int(math.floor(faulty_replicas))
            command += 'cp shards/config0/system.config.forscript shards/s{0}/system.config.forscript;'.format(i)
            command += 'printf "system.servers.num = {1}\n" >> shards/s{0}/system.config.forscript;'.format(i, len(instances))
            command += 'printf "system.servers.f = {1}\n" >> shards/s{0}/system.config.forscript;'.format(i, faulty_replicas)
            command += 'printf "system.initial.view = {1}\n" >> shards/s{0}/system.config.forscript;'.format(i, initial_view)
            command += 'cp shards/s{0}/system.config.forscript shards/s{0}/system.config;'.format(i)

        return command

    def launch(self, count, key_name):
        self._log("Launching {} instances...".format(count))
        self.ec2.create_instances(
            ImageId=_jessie_mapping[self.aws_region], # Debian 8.7
            InstanceType='t2.medium',
            MinCount=count,
            MaxCount=count,
            KeyName=key_name,
            SecurityGroups=['chainspace'],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'type', 'Value': 'chainspace'},
                        {'Key': 'network_id', 'Value': self.network_id},
                        {'Key': 'Name', 'Value': 'Chainspace node (network: {})'.format(self.network_id)},
                    ]
                }
            ]
        )
        self._log("Launched {} instances.".format(count))

    def install_deps(self):
        self._log("Installing Chainspace dependencies on all nodes...")
        command = 'export DEBIAN_FRONTEND=noninteractive;'
        command += 'export DEBIAN_PRIORITY=critical;'
        command += 'until '
        command += 'sudo -E apt update'
        command += '&& sudo -E apt --yes --force-yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" install -t jessie-backports openjdk-8-jdk'
        command += '&& sudo -E apt --yes --force-yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" install git python-pip maven screen psmisc'
        command += '; do :; done'
        self.ssh_exec(command)
        self._log("Installed Chainspace dependencies on all nodes.")

    def install_core(self):
        self._log("Installing Chainspace core on all nodes...")
        command = 'git clone https://github.com/sheharbano/byzcuit chainspace;'
        command += 'sudo pip install chainspace/chainspacecontract;'
        command += 'sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java;'
        command += 'cd ~/chainspace/chainspacecore; export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64; mvn package assembly:single;'
        command += 'cd ~; mkdir contracts;'
        command += 'cp ~/chainspace/chainspacemeasurements/chainspacemeasurements/contracts/simulator.py contracts'
        self.ssh_exec(command)
        self._log("Installed Chainspace core on all nodes.")

    def ssh_connect(self):
        self._log("Initiating SSH connection on all nodes...")
        args = [(self._single_ssh_connect, instance) for instance in self._get_running_instances()]
        pool = Pool(ChainspaceNetwork.threads)
        pool.map(_multi_args_wrapper, args)
        pool.close()
        pool.join()
        self._log("Initiated SSH connection on all nodes.")

    def ssh_exec(self, command):
        self._log("Executing command on all nodes: {}".format(command))
        args = [(self._single_ssh_exec, instance, command) for instance in self._get_running_instances()]
        pool = Pool(ChainspaceNetwork.threads)
        result = pool.map(_multi_args_wrapper, args)
        pool.close()
        pool.join()
        self._log("Executed command on all nodes: {}".format(command))

        return result

    def ssh_close(self):
        self._log("Closing SSH connection on all nodes...")
        args = [(self._single_ssh_close, instance) for instance in self._get_running_instances()]
        pool = Pool(ChainspaceNetwork.threads)
        pool.map(_multi_args_wrapper, args)
        pool.close()
        pool.join()
        self._log("Closed SSH connection on all nodes.")

    def terminate(self):
        self._log("Terminating all nodes...")
        self._get_all_instances().terminate()
        self._log("All nodes terminated.")

    def start(self):
        self._log("Starting all nodes...")
        self._get_stopped_instances().start()
        self._log("Started all nodes.")

    def stop(self):
        self._log("Stopping all nodes...")
        self._get_running_instances().stop()
        self._log("Stopped all nodes.")

    def start_core_all(self):
        self._log("Starting Chainspace core on all nodes...")
        command = 'screen -dmS chainspacecore java -cp chainspace/chainspacecore/lib/BFT-SMaRt.jar:chainspace/chainspacecore/target/chainspace-1.0-SNAPSHOT-jar-with-dependencies.jar uk.ac.ucl.cs.sec.chainspace.bft.TreeMapServer chainspace/chainspacecore/ChainSpaceConfig/config.txt'
        self.ssh_exec(command)
        self._log("Started Chainspace core on all nodes.")

    def start_core(self):
        self._log("Starting Chainspace core on all shards...")
        args = [(self._start_shard, shard) for shard in self.shards.values()]
        pool = Pool(ChainspaceNetwork.threads)
        pool.map(_multi_args_wrapper, args)
        pool.close()
        pool.join()
        self._log("Started Chainspace core on all shards.")

    def _start_shard(self, shard):
        command = 'screen -dmS chainspacecore java -cp chainspace/chainspacecore/lib/BFT-SMaRt.jar:chainspace/chainspacecore/target/chainspace-1.0-SNAPSHOT-jar-with-dependencies.jar uk.ac.ucl.cs.sec.chainspace.bft.TreeMapServer chainspace/chainspacecore/ChainSpaceConfig/config.txt'
        for instance in shard:
                self._single_ssh_exec(instance, command)
                time.sleep(0.5)

    def stop_core(self):
        self._log("Stopping Chainspace core on all nodes...")
        command = 'killall java' # hacky; should use pid file
        self.ssh_exec(command)
        self._log("Stopping Chainspace core on all nodes.")

    def uninstall_core(self):
        self._log("Uninstalling Chainspace core on all nodes...")
        command = 'rm -rf chainspace;'
        command += 'sudo pip uninstall -y chainspacecontract;'
        command += 'rm -rf contracts;'
        command += 'rm -rf config;';
        self.ssh_exec(command)
        self._log("Uninstalled Chainspace core on all nodes.")

    def clean_state_core(self):
        self._log("Resetting Chainspace core state...")
        command = ''
        command += 'rm database.sqlite; rm simplelog;'
        self.ssh_exec(command)
        self._log("Reset Chainspace core state.")

    def config_local_client(self, directory):
        os.system(self._config_shards_command(directory))

    def config_core(self, shards, nodes_per_shard):
        instances = [instance for instance in self._get_running_instances()]
        shuffled_instances = random.sample(instances, shards * nodes_per_shard)

        if shards * nodes_per_shard > len(instances):
            raise ValueError("Number of total nodes exceeds the number of running instances.")

        self.shards = {}
        for shard in range(shards):
            self.shards[shard] = shuffled_instances[shard*nodes_per_shard:(shard+1)*nodes_per_shard]

        for i, instances in enumerate(self.shards.values()):
            for j, instance in enumerate(instances):
                command = self._config_shards_command('chainspace/chainspacecore/ChainSpaceConfig')
                command += 'printf "shardConfigFile chainspace/chainspacecore/ChainSpaceConfig/shardConfig.txt\nthisShard {0}\nthisReplica {1}\n" > config.txt;'.format(i, j)
                command += 'cd ../../../;'
                command += 'rm -rf config;'
                command += 'cp -r chainspace/chainspacecore/ChainSpaceConfig/shards/s{0} config;'.format(i)
                self._single_ssh_exec(instance, command)

    def config_me(self, directory='/home/admin/chainspace/chainspacecore/ChainSpaceClientConfig'):
        return os.system(self._config_shards_command(directory))

    def get_tps_set(self):
        tps_set = []
        for shard in self.shards.itervalues():
            instance = shard[0]
            tps = self._single_ssh_exec(instance, 'python chainspace/chainspacemeasurements/chainspacemeasurements/tps.py')[1]
            tps = float(tps.strip())
            tps_set.append(tps)

        return tps_set

    def get_tpsm_set(self):
        tps_set = []
        for shard in self.shards.itervalues():
            instance = shard[0]
            tps = self._single_ssh_exec(instance, 'python chainspace/chainspacemeasurements/chainspacemeasurements/tpsm.py')[1]
            tps = float(tps.strip())
            tps_set.append(tps)

        return tps_set

    def get_r0_logs(self):
        logs = []
        for shard in self.shards.itervalues():
            instance = shard[0]
            log = self._single_ssh_exec(instance, 'cat simplelog')[1]
            logs.append(log)

        return logs


def _multi_args_wrapper(args):
    return args[0](*args[1:])


def _safe_print(message):
    sys.stdout.write('{}\n'.format(message))


_jessie_mapping = {
    'ap-northeast-1': 'ami-dbc0bcbc',
    'ap-northeast-2': 'ami-6d8b5a03',
    'ap-south-1': 'ami-9a83f5f5',
    'ap-southeast-1': 'ami-0842e96b',
    'ap-southeast-2': 'ami-881317eb',
    'ca-central-1': 'ami-a1fe43c5',
    'eu-central-1': 'ami-5900cc36',
    'eu-west-1': 'ami-402f1a33',
    'eu-west-2': 'ami-87848ee3',
    'sa-east-1': 'ami-b256ccde',
    'us-east-1': 'ami-b14ba7a7',
    'us-east-2': 'ami-b2795cd7',
    'us-west-1': 'ami-94bdeef4',
    'us-west-2': 'ami-221ea342',
}
