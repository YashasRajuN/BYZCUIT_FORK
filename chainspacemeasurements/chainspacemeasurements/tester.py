import os
import operator
import time
import sys
import traceback
import json

from chainspacemeasurements import dumper
from chainspacemeasurements.instances import ChainspaceNetwork, SHARD
from chainspacemeasurements.dumpparser import parse_tcpdump


def parse_client_simplelog(filename):
    data = open(filename).readlines()[2:]
    txes = {}
    for line in data:
        record = line.split()
        txes[record[1]] = int(record[0])

    return txes


class Tester(object):
    def __init__(self, network, core_directory='/home/admin/chainspace/chainspacecore', outfile='out'):
        self.outfh = open(outfile, 'a')
        self.core_directory = core_directory
        self.network = network

        network.logging = False

        network.ssh_connect(0)
        network.ssh_connect(1)

        # freshen state
        self.stop_tcpdump()
        self.stop_clients()
        network.stop_core()
        time.sleep(2)
        network.clean_state_core(SHARD)

    def start_clients(self, num):
        self.network.config_clients(num)
        n.start_clients()

    def stop_clients(self):
        n.stop_clients()

    def start_tcpdump(self):
        os.system('sudo rm ' + self.core_directory + '/tcpdump_log')
        os.system('screen -dmS tcpdump bash -c "sudo tcpdump -i eth0 -A -tt | grep \'\' > ' + self.core_directory + '/tcpdump_log"')

    def stop_tcpdump(self):
        os.system('sudo killall tcpdump')

    def measure_client_latency(self, min_batch, max_batch, batch_step, runs):
        latency_times_set_set = []

        for batch_size in range(min_batch, max_batch+1, batch_step):
            latency_times_set = []
            for i in range(runs):
                print "Running client latency measurements for batch size {0} (run {1}).".format(batch_size, i)

                num_transactions = max_batch*3

                self.network.config_core(2, 4)
                self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                self.network.start_core()
                time.sleep(10)
                self.start_tcpdump()
                self.start_clients(2)
                time.sleep(10)
                dumper.simulation_batched(self.network, num_transactions, inputs_per_tx=1, outputs_per_tx=0, batch_size=batch_size, batch_sleep=1)
                time.sleep(20)
                self.stop_clients()
                self.stop_tcpdump()
                self.network.stop_core()
                time.sleep(2)
                self.network.clean_state_core(SHARD)

                tcpdump_txes = parse_tcpdump(self.core_directory + '/tcpdump_log')
                client_txes = parse_client_simplelog(self.core_directory + '/simplelog_client')

                latency_times = []
                for tx, t in tcpdump_txes.iteritems():
                    try:
                        latency_times.append((tcpdump_txes[tx] - client_txes[tx])/1000.0)
                    except Exception:
                        pass

                latency_times_set.append(latency_times)
                print latency_times

            latency_times_set_set.append(latency_times_set)

        self.outfh.write(json.dumps(latency_times_set_set))
        return latency_times_set_set

    def measure_shard_scaling(self, min_shards, max_shards, runs, inputs_per_tx=1, outputs_per_tx=0):
        tps_sets_sets = []
        for num_shards in range(min_shards, max_shards+1):
            tps_sets = []

            for i in range(runs):
                try:
                    print "Running measurements for {0} shards (run {1}).".format(num_shards, i)
                    self.network.config_core(num_shards, 4)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    batch_size = 100*num_shards
                    num_transactions = 300*num_shards

                    time.sleep(10)
                    self.start_clients(num_shards)
                    time.sleep(10)
                    dumper.simulation_batched(self.network, num_transactions, inputs_per_tx, outputs_per_tx, batch_size=batch_size, batch_sleep=1)
                    time.sleep(20)
                    self.stop_clients()

                    tps_set = self.network.get_tpsm_set()
                    tps_sets.append(tps_set)
                    print "Result for {0} shards (run {1}): {2}".format(num_shards, i, tps_set)
                except Exception:
                    traceback.print_exc()
                finally:
                    try:
                        self.network.stop_core()
                        time.sleep(2)
                        self.network.clean_state_core(SHARD)
                    except:
                        # reset connection
                        for i in range(5):
                            try:
                                self.network.ssh_close()
                                self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.outfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_node_scaling(self, num_shards, min_nodes, max_nodes, runs, step=1):
        tps_sets_sets = []
        for num_nodes in range(min_nodes, max_nodes+1, step):
            tps_sets = []

            for i in range(runs):
                try:
                    print "Running measurements for {2} nodes in {0} shards (run {1}).".format(num_shards, i, num_nodes)
                    self.network.config_core(num_shards, num_nodes)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    batch_size = 100*num_shards
                    num_transactions = 300*num_shards

                    time.sleep(10)
                    self.start_clients(num_shards)
                    time.sleep(10)
                    dumper.simulation_batched(self.network, num_transactions, 1, 0, batch_size=batch_size, batch_sleep=1)
                    time.sleep(20)
                    self.stop_clients()

                    tps_set = self.network.get_tps_set()
                    tps_sets.append(tps_set)
                    print "Result for {3} nodes in {0} shards (run {1}): {2}".format(num_shards, i, tps_set, num_nodes)
                except Exception:
                    traceback.print_exc()
                finally:
                    try:
                        self.network.stop_core()
                        time.sleep(2)
                        self.network.clean_state_core(SHARD)
                    except:
                        # reset connection
                        for i in range(5):
                            try:
                                self.network.ssh_close()
                                self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.outfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_input_scaling(self, num_shards, min_inputs, max_inputs, runs, case=None):
        tps_sets_sets = []
        for num_inputs in range(min_inputs, max_inputs+1):
            tps_sets = []

            if case is None:
                shards_per_tx = None
            elif case == 'best':
                shards_per_tx = 1
            elif case == 'worst':
                shards_per_tx = num_shards

            for i in range(runs):
                try:
                    print "Running measurements for {2} inputs across {0} shards (run {1}).".format(num_shards, i, num_inputs)
                    self.network.config_core(num_shards, 4)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    batch_size = 100*num_shards
                    num_transactions = 300*num_shards

                    time.sleep(10)
                    self.start_clients(num_shards)
                    time.sleep(10)
                    dumper.simulation_batched(self.network, num_transactions, num_inputs, 0, batch_size=batch_size, batch_sleep=1)
                    time.sleep(20)
                    self.stop_clients()

                    txes = {}
                    logs = self.network.get_r0_logs()
                    for log in logs:
                        for line in log.splitlines():
                            line = line.strip()
                            if line == '':
                                continue
                            records = line.split()
                            if records[1] not in txes:
                                txes[records[1]] = int(records[0])

                    tps_set = self.network.get_tpsm_set()
                    tps_sets.append(tps_set)
                    print "Result for {0} shards (run {1}): {2}".format(num_shards, i, tps_set)
                except Exception:
                    traceback.print_exc()
                finally:
                    try:
                        self.network.stop_core()
                        time.sleep(2)
                        self.network.clean_state_core(SHARD)
                    except:
                        # reset connection
                        for i in range(5):
                            try:
                                self.network.ssh_close()
                                self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.outfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets


if __name__ == '__main__':
    if sys.argv[1] == 'shardscaling':
        min_shards = int(sys.argv[2])
        max_shards = int(sys.argv[3])
        runs = int(sys.argv[4])
        outfile = sys.argv[5]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_shard_scaling(min_shards, max_shards, runs)
    elif sys.argv[1] == 'shardscaling_mi':
        inputs_per_tx = int(sys.argv[2])
        min_shards = int(sys.argv[3])
        max_shards = int(sys.argv[4])
        runs = int(sys.argv[5])
        outfile = sys.argv[6]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_shard_scaling(min_shards, max_shards, runs, inputs_per_tx)
    elif sys.argv[1] == 'shardscaling_mico':
        inputs_per_tx = int(sys.argv[2])
        outputs_per_tx = int(sys.argv[3])
        min_shards = int(sys.argv[4])
        max_shards = int(sys.argv[5])
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_shard_scaling(min_shards, max_shards, runs, inputs_per_tx, outputs_per_tx)
    elif sys.argv[1] == 'inputscaling':
        num_shards = int(sys.argv[2])
        min_inputs = int(sys.argv[3])
        max_inputs = int(sys.argv[4])
        runs = int(sys.argv[5])
        outfile = sys.argv[6]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_input_scaling(num_shards, min_inputs, max_inputs, runs)
    elif sys.argv[1] == 'inputscaling_f':
        num_shards = int(sys.argv[2])
        min_inputs = int(sys.argv[3])
        max_inputs = int(sys.argv[4])
        case = sys.argv[5]
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_input_scaling(num_shards, min_inputs, max_inputs, runs, case=case)
    elif sys.argv[1] == 'nodescaling':
        num_shards = int(sys.argv[2])
        min_nodes = int(sys.argv[3])
        max_nodes = int(sys.argv[4])
        step = int(sys.argv[5])
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_node_scaling(num_shards, min_nodes, max_nodes, runs, step=step)
    elif sys.argv[1] == 'clientlatency':
        min_batch = int(sys.argv[2])
        max_batch = int(sys.argv[3])
        batch_step = int(sys.argv[4])
        runs = int(sys.argv[5])
        outfile = sys.argv[6]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print t.measure_client_latency(min_batch, max_batch, batch_step, runs)
