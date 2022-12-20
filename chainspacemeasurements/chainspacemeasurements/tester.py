# my tester.py

import os
import operator
import time
import sys
import traceback
import json
import numpy as np


from chainspacemeasurements import dumper
from chainspacemeasurements.instances import ChainspaceNetwork, SHARD
from chainspacemeasurements.dumpparser import parse_tcpdump
from os import walk

def parse_client_simplelog(filename):
    data = open(filename).readlines()[2:]
    txes = {}
    for line in data:
        record = line.split()
        txes[record[1]] = int(record[0])

    return txes


class Tester(object):
    def __init__(self, network, core_directory='/home/yash/chainspace/chainspacecore', tpsfile='tps',latencyfile='lat',outfile='out'):
        self.outfh = open(outfile, 'w')
        self.tpsfh = open(tpsfile, 'w')
        self.latfh = open(latencyfile, 'w')
        self.core_directory = core_directory
        self.network = network

        network.logging = True

        network.ssh_connect(0)
        network.ssh_connect(1)

        # freshen state
        self.stop_tcpdump()
        self.stop_clients()
        network.stop_core()
        time.sleep(2)
        network.clean_state_core(SHARD)

    def start_clients(self):
        print(len(self.network.shards))
        self.network.config_clients(len(self.network.shards)*8)
        n.start_clients()

    def stop_clients(self):
        n.stop_clients()

    def start_tcpdump(self):
        os.system('sudo rm ' + self.core_directory + '/tcpdump_log')
        os.system('screen -dmS tcpdump bash -c "sudo tcpdump -i eth0 -A -tt | grep \'\' > ' + self.core_directory + '/tcpdump_log"')

    def stop_tcpdump(self):
        os.system('sudo killall tcpdump')

    def measure_client_latency(self, shards, inputs, outputs, min_batch, max_batch, batch_step, runs,shardListPath, defences=False):
        if defences:
            create_dummy_objects = 1
        else:
            create_dummy_objects = 0
        latency_times_set_set = []

        for batch_size in range(min_batch, max_batch+1, batch_step):
            latency_times_set = []
            for i in range(runs):
                print ("Running client latency measurements for batch size {0} (run {1}).".format(batch_size, i))

                num_transactions = max_batch*3

                self.network.config_core(shards, 2)
                self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                self.network.start_core()
                time.sleep(10)
                self.start_clients()
                time.sleep(10)
                dumper.simulation_batched_dummy(self.network, inputs_per_tx=inputs, outputs_per_tx=outputs, shardListPath=shardListPath,batch_size=min_batch, batch_sleep=1, num_transactions=num_transactions, create_dummy_objects=create_dummy_objects)

                #dumper.simulation_batched(self.network, num_transactions, inputs_per_tx=inputs, outputs_per_tx=outputs, shardListPath,batch_size=min_batch )
                #simulation_batched(network, num_transactions, inputs_per_tx, outputs_per_tx, shardListPath, batch_size=4000, batch_sleep=1, input_object_mode=0, create_dummy_objects=0, num_dummy_objects=0, output_object_mode=0)
                time.sleep(20)
                self.stop_clients()
                self.network.stop_core()
                time.sleep(2)
                self.network.clean_state_core(SHARD)

                latency_times = self.network.get_latency()
                #latency_times = list(map(float, self.network.get_latency()))
                #client_txes = parse_client_simplelog(self.core_directory + '/simplelog_client')
                #latency_times1=[]
                #for t in range(0,len(latency_times)):
                 #   latency_times1.append((latency_times[t] - client_txes[t])/1000.0)
                #latency_times_set.append(latency_times1)
                #for x in latency_times:
                #    float(x)=float(x)/1000.0
                #latency_times=latency_times/1000.0
                latency_times_set.append(latency_times)
                print (latency_times)

            latency_times_set_set.append(latency_times_set)

        self.tpsfh.write(json.dumps(latency_times_set_set))
        return latency_times_set_set

    def measure_shard_scaling(self, min_shards, max_shards, runs,shardListPath, inputs_per_tx=1, outputs_per_tx=0, defences=False):
        if defences:
            create_dummy_objects = 1
        else:
            create_dummy_objects = 0
        tps_sets_sets = []
        for num_shards in range(min_shards, max_shards+1):
            tps_sets = []

            for i in range(runs):
                try:
                    print ("Running measurements for {0} shards (run {1}).".format(num_shards, i))
                    self.network.config_core(num_shards, 2)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    time.sleep(10)
                    self.start_clients()
                    time.sleep(10)
                    #dumper.simulation_batched(self.network,num_transactions=len(shardListPath),shardListPath=shardListPath, inputs_per_tx, outputs_per_tx, create_dummy_objects=create_dummy_objects)
                    
                    dumper.simulation_batched_dummy(self.network, inputs_per_tx=inputs_per_tx, outputs_per_tx=outputs_per_tx,shardListPath=shardListPath,num_transactions=len(shardListPath))
                    #dumper.simulation_batched_dummy(self.network, inputs_per_tx=inputs, outputs_per_tx=outputs, shardListPath=shardListPath,batch_size=min_batch, batch_sleep=1, num_transactions=num_transactions, create_dummy_objects=create_dummy_objects)
                    time.sleep(20)
                    self.stop_clients()

                    tps_set = self.network.get_tpsm_set()
                    print("no error in tpsm set")
                    print(tps_set)
                    time.sleep(20)
                    tps_sets.append(tps_set)
                    print ("Result for {0} shards (run {1}): {2}".format(num_shards, i, tps_set))
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
                                #self.network.ssh_close()
                                #self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.tpsfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_node_scaling(self, num_shards, min_nodes, max_nodes, runs,shardListPath):
        tps_sets_sets = []
        for num_nodes in range(min_nodes, max_nodes+1, 1):
            tps_sets = []

            for i in range(runs):
                try:
                    print("Running measurements for {2} nodes in {0} shards (run {1}).".format(num_shards, i, num_nodes))
                    self.network.config_core(num_shards, num_nodes)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    time.sleep(10)
                    self.start_clients()
                    time.sleep(10)
                    dumper.simulation_batched(self.network,num_transactions=len(shardListPath),shardListPath=shardListPath)
                    time.sleep(20)
                    self.stop_clients()

                    tps_set = self.network.get_tps_set()
                    tps_sets.append(tps_set)
                    print ("Result for {3} nodes in {0} shards (run {1}): {2}".format(num_shards, i, tps_set, num_nodes))
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

        self.tpsfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_input_scaling(self, num_shards, min_inputs, max_inputs, num_outputs, runs,shardListPath, case=None, defences=False):
        if defences:
            create_dummy_objects = 1
        else:
            create_dummy_objects = 0
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
                    print ("Running measurements for {2} inputs across {0} shards (run {1}).".format(num_shards, i, num_inputs))
                    self.network.config_core(num_shards, 2)
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    self.network.start_core()

                    time.sleep(10)
                    self.start_clients()
                    time.sleep(10)
                    dumper.simulation_batched_dummy(self.network,inputs_per_tx= num_inputs,outputs_per_tx= num_outputs,shardListPath=shardListPath,num_transactions=len(shardListPath))
                    time.sleep(20)
                    self.stop_clients()

                    tps_set = self.network.get_tpsm_set()
                    tps_sets.append(tps_set)
                    print("Result for {0} shards (run {1}): {2}".format(num_shards, i, tps_set))
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
                                #self.network.ssh_close()
                                #self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                time.sleep(10)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.tpsfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_bano(self, num_shards, runs,shardListPath):
        tps_sets_sets = []
        for num_dummies in range(1, num_shards):
            tps_sets = []

            for i in range(runs):
                try:
                    print ("Running measurements for {2} dummy objects across {0} shards (run {1}).".format(num_shards, i, num_dummies))
                    print ("config core")
                    self.network.config_core(num_shards, 2)
                    print( "config me")
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    print ("start core")
                    self.network.start_core()

                    time.sleep(10)
                    print ("start clients")
                    self.start_clients()
                    time.sleep(10)
                    print( "start simulation")
                    dumper.simulation_batched(self.network, 12000,1, 1,shardListPath, create_dummy_objects=1, num_dummy_objects=num_dummies, output_object_mode=-1)
                    #simulation_batched(network, num_transactions, inputs_per_tx, outputs_per_tx, shardListPath, batch_size=4000, batch_sleep=1, input_object_mode=0, create_dummy_objects=0, num_dummy_objects=0, output_object_mode=0)
                    print ("simulation done")
                    time.sleep(20)
                    print ("stop clients")
                    self.stop_clients()

                    tps_set = self.network.get_tpsm_set()
                    tps_sets.append(tps_set)
                    print ("Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, tps_set))
                except Exception:
                    traceback.print_exc()
                finally:
                    try:
                        self.network.stop_core()
                        time.sleep(2)
                        self.network.clean_state_core(SHARD)
                        self.network.ssh_close(1)
                        self.network.ssh_close(1)

                    except:
                        # reset connection
                        for i in range(5):
                            try:
                                #self.network.ssh_close()
                                #self.network.ssh_connect()
                                self.network.stop_core()
                                time.sleep(2)
                                self.network.clean_state_core(SHARD)
                                break
                            except:
                                time.sleep(5)

            tps_sets_sets.append(tps_sets)

        self.tpsfh.write(json.dumps(tps_sets_sets))
        return tps_sets_sets

    def measure_sharding12(self, min_validators, max_validators, num_shards, runs,shardListPath):

        nbremptyLat = 0
        nbremptyTps = 0
        tps_sets_sets = []
        latency_times_sets_sets = []
        allLatency = []
        allTps = []
        for validators in range(min_validators,max_validators+1):
            for num_dummies in range(1, 2): #num_shards
                tps_sets = []
                latency_times_sets = []
                for i in range(runs):
                    try:
                        print("-------------------------------------------------------------------")
                        print("----------------        run "+str(i)+"          ------------")
                        print("-------------------------------------------------------------------")
                        print ("----------------Running measurements for {2} dummy objects across {0} shards (run {1}).".format(num_shards, i, num_dummies))
                        print ("config core")
                        self.network.config_core(num_shards, validators)
                        print ("config me")
                        self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                        print ("start core")
                        self.network.start_core()

                        #time.sleep(5)
                        print ("-------start clients")
                        self.start_clients()
                        time.sleep(10)
                        print ("--------start simulation")
                        #dumper.simulation_batched(network, inputs_per_tx, outputs_per_tx, num_transactions=None, batch_size=4000, batch_sleep=1, input_object_mode=0, create_dummy_objects=0, num_dummy_objects=0, output_object_mode=0):
                        print("----------------------------------------------------------------------------------------------------------------------  "+str(shardListPath))
                        #dumper.simulation_batched(self.network,num_transactions, 1, 1, shardListPath)
                        #print(len(open(shardListPath).readlines()))
                        #time.sleep(20)
                        dumper.simulation_batched(self.network,len(open(shardListPath).readlines()),shardListPath)
                        print ("simulation done")
                        time.sleep(20)
                        print ("stop clients")
                        self.stop_clients()

                        tps_set = self.network.get_tpsm_set()

                        if (len(tps_set) == 0 or sum(tps_set) == 0):
                            print("tps empty")
                            time.sleep(20)
                            nbremptyTps = nbremptyTps +1
                        else :
                            tps_set_avg = sum(tps_set) / len(tps_set)
                            tps_sets.append(tps_set_avg)
                            allTps.extend(tps_set)


                        latency_times = self.network.get_latency()

                        if (len(latency_times)==0):
                            print("latency empty")
                            time.sleep(20)
                            nbremptyLat = nbremptyLat +1
                        else : 
                            latency_times_avg = sum(latency_times) / len(latency_times)
                            latency_times_sets.append(latency_times_avg)
                            allLatency.extend(latency_times)

                        #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, tps_set)
                        #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, latency_times_set)
                        
                    except Exception:
                        traceback.print_exc()
                    finally:
                        try:
                            self.network.stop_core()
                            time.sleep(5)
                            self.network.clean_state_core(SHARD)
                            time.sleep(2)
                        except:
                            # reset connection
                            for i in range(5):
                                try:
                                    #instead of resetting, sleep for 20 seconds before
                                    #self.network.ssh_close()
                                    #self.network.ssh_connect()
                                    self.network.stop_core()
                                    time.sleep(10)
                                    self.network.clean_state_core(SHARD)
                                    break
                                except:
                                    time.sleep(5)

            tps_sets_avg = sum(tps_sets) / len(tps_sets)
            tps_sets_sets.append(tps_sets_avg)
            latency_times_sets_avg = sum(latency_times_sets) / len(latency_times_sets)
            latency_times_sets_sets.append(latency_times_sets_avg)

        for x in tps_sets_sets:
            print ("TPS "+str(x))
        print(allTps)
        stdTps = np.std(np.array(allTps))
        stdLatency = np.std(np.array(allLatency))
        self.tpsfh.write("tps: "+str(tps_sets_sets)+" \n")
        self.tpsfh.write("std: "+str(stdTps)+" \n")
        self.tpsfh.write("latency: "+str(latency_times_sets_sets)+" \n")#son.dumps
        self.tpsfh.write("std: "+str(stdLatency)+" \n")
        self.tpsfh.write("  \n")
        self.tpsfh.write(str(allTps)+" \n")
        self.tpsfh.write("  \n")
        self.tpsfh.write("number empty tps: "+str(nbremptyTps)+" \n")
        self.tpsfh.write("number empty latency: "+str(nbremptyLat)+" \n")

        print("number of empty Tps "+str(nbremptyTps))
        print("nbumber of empty Latency "+str(nbremptyLat))

        #self.latfh.write(json.dumps(latency_times_sets_sets))
        return tps_sets_sets

    def measure_sharding(self, min_validators, max_validators, num_shards, runs,shardListPath):

        tps_sets_sets = []
        latency_times_sets_sets = []

        for validators in range(min_validators,max_validators+1):
            print ("Start test validators "+str(validators))
#            for num_dummies in range(1, num_shards):
            tps_sets = []
            latency_times_sets = []
#            for i in range(runs):
            #file_list = os.listdir(shardListPath)
#            for r,d,f in walk (shardListPath):
            i=0
            for i in range(2):
                try:
    #                    print "Running measurements for {2} dummy objects across {0} shards (run {1}).".format(num_shards, i, num_dummies)
    #                self.network.ssh_connect(0)
    #                self.network.ssh_connect(1)
                    print(")))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))")
                    print("))))))))))))))))))))        run "+str(i)+"          )))))))))))))))))))))))))))")
                    print(")))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))")
                    print ("config core")
                    self.network.config_core(num_shards, validators)
                    print ("config me")
                    self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                    print ("start core")
                    self.network.start_core()

    #                time.sleep(10)
                    print ("start clients")
                    self.start_clients()
                    time.sleep(10)
                    print ("start simulation")
    #                print shardListPath+"/"+file
    #                print len(open(shardListPath+"/"+file).readlines())
                    dumper.simulation_batched(self.network,len(open(shardListPath).readlines()),shardListPath)
    #                dumper.simulation_batched(self.network,len(open(shardListPath+"/"+file).readlines()), shardListPath+"/"+file)
                    print ("simulation done")
                    time.sleep(20)
                    print ("stop clients")
                    self.stop_clients()

    #                log = self.network.get_r0_logs()
    #                print log
                    tps_set = self.network.get_tpsm_set()
                    tps_set_avg = sum(tps_set) / len(tps_set)
                    #print "Avg set "+str(tps_set_avg)
                    tps_sets.append(tps_set_avg)

                    latency_times = self.network.get_latency()
                    latency_times_avg = sum(latency_times) / len(latency_times)
                    #print "Latency: {0}".format(latency_times)
                    latency_times_sets.append(latency_times_avg)

                    #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, tps_set)
                    #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, latency_times_set)
                except Exception:
                    traceback.print_exc()
                finally:
                    try:
                        self.network.stop_core()
                        time.sleep(2)
                        self.network.clean_state_core(SHARD)
                        #self.network.ssh_close(0)
                        #self.network.ssh_close(1)
                        time.sleep(100)
                    except:
                        # reset connection
    #                            for i in range(5):
                        try:
                            #self.network.ssh_close()

                            #self.network.ssh_connect()
                            self.network.stop_core()
                            time.sleep(20)
                            self.network.clean_state_core(SHARD)
                            time.sleep(200)
                            break
                        except:
                            time.sleep(50)

                tps_sets_avg = sum(tps_sets) / len(tps_sets)
                tps_sets_sets.append(tps_sets_avg)
                latency_times_sets_avg = sum(latency_times_sets) / len(latency_times_sets)
                latency_times_sets_sets.append(latency_times_sets_avg)

                for x in tps_sets_sets:
                    print ("TPS "+str(x))

        self.tpsfh.write(json.dumps(tps_sets_sets))
        self.latfh.write(json.dumps(latency_times_sets_sets))
        return tps_sets_sets

    def measure_sergi(self, min_validators, max_validators,num_transactions, num_shards, runs, mode,shardListPath):

        tps_sets_sets = []
        latency_times_sets_sets = []

        for validators in range(min_validators,max_validators+1):
            print ("Start test validators "+str(validators))
            for num_dummies in range(1, num_shards):
                tps_sets = []
                latency_times_sets = []
                for i in range(runs):
                    try:
                        print ("Running measurements for {2} dummy objects across {0} shards (run {1}).".format(num_shards, i, num_dummies))
                        print ("config core")
                        self.network.config_core(num_shards, validators)
                        print ("config me")
                        self.network.config_me(self.core_directory + '/ChainSpaceClientConfig')
                        print ("start core")
                        self.network.start_core()

                        time.sleep(10)
                        print ("start clients")
                        self.start_clients()
                        time.sleep(10)
                        print ("start simulation")
                        #dumper.simulation_batched(network, inputs_per_tx, outputs_per_tx, num_transactions=None, batch_size=4000, batch_sleep=1, input_object_mode=0, create_dummy_objects=0, num_dummy_objects=0, output_object_mode=0):

                        dumper.simulation_batched(self.network,num_transactions, 2, 2, shardListPath, input_object_mode=mode,create_dummy_objects=0, output_object_mode=mode)
                        print ("simulation done")
                        time.sleep(20)
                        print ("stop clients")
                        self.stop_clients()

                        tps_set = self.network.get_tpsm_set()
                        tps_set_avg = sum(tps_set) / len(tps_set)
                        #print "Avg set "+str(tps_set_avg)
                        tps_sets.append(tps_set_avg)

                        latency_times = self.network.get_latency()
                        latency_times_avg = sum(latency_times) / len(latency_times)
                        #print "Latency: {0}".format(latency_times)
                        latency_times_sets.append(latency_times_avg)

                        #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, tps_set)
                        #print "Result for {0} dummy objects (run {1}): {2}".format(num_dummies, i, latency_times_set)
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
                                    #self.network.ssh_close()
                                    #self.network.ssh_connect()
                                    self.network.stop_core()
                                    time.sleep(20)
                                    self.network.clean_state_core(SHARD)
                                    break
                                except:
                                    time.sleep(50)

            tps_sets_avg = sum(tps_sets) / len(tps_sets)
            tps_sets_sets.append(tps_sets_avg)
            latency_times_sets_avg = sum(latency_times_sets) / len(latency_times_sets)
            latency_times_sets_sets.append(latency_times_sets_avg)

        for x in tps_sets_sets:
            print ("TPS "+str(x))

        self.tpsfh.write(json.dumps(tps_sets_sets))
        self.latfh.write(json.dumps(latency_times_sets_sets))
        return tps_sets_sets
        
if __name__ == '__main__':
    if sys.argv[1] == 'shardscaling':
        min_shards = int(sys.argv[2])
        max_shards = int(sys.argv[3])
        runs = int(sys.argv[4])
        shardListPath=sys.argv[5]
        outfile = sys.argv[6]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_shard_scaling(min_shards, max_shards, runs,shardListPath))
        #tester.py shardscaling 2 15 2 


    elif sys.argv[1] == 'shardscaling_mi':
        inputs_per_tx = int(sys.argv[2])
        min_shards = int(sys.argv[3])
        max_shards = int(sys.argv[4])
        runs = int(sys.argv[5])
        outfile = sys.argv[6]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_shard_scaling(min_shards, max_shards, runs, inputs_per_tx))
    elif sys.argv[1] == 'shardscaling_mico':
        inputs_per_tx = int(sys.argv[2])
        outputs_per_tx = int(sys.argv[3])
        min_shards = int(sys.argv[4])
        max_shards = int(sys.argv[5])
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_shard_scaling(min_shards, max_shards, runs, inputs_per_tx, outputs_per_tx))
    elif sys.argv[1] == 'shardscaling_micod':
        inputs_per_tx = int(sys.argv[2])
        outputs_per_tx = int(sys.argv[3])
        min_shards = int(sys.argv[4])
        max_shards = int(sys.argv[5])
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_shard_scaling(min_shards, max_shards, runs, inputs_per_tx, outputs_per_tx, defences=True))
    elif sys.argv[1] == 'inputscaling':
        num_shards = int(sys.argv[2])
        min_inputs = int(sys.argv[3])
        max_inputs = int(sys.argv[4])
        num_outputs = int(sys.argv[5])
        runs = int(sys.argv[6])
        shardListPath = sys.argv[7]
        outfile = sys.argv[8]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_input_scaling(num_shards, min_inputs, max_inputs, num_outputs, runs,shardListPath))
        #python3 tester.py inputscaling 3 1 10 2 2 
    elif sys.argv[1] == 'nodescaling':
        num_shards = int(sys.argv[2])
        min_nodes = int(sys.argv[3])
        max_nodes = int(sys.argv[4])
        step = int(sys.argv[5])
        runs = int(sys.argv[6])
        shardListPath = sys.argv[7]
        outfile = sys.argv[8]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_node_scaling(num_shards, min_nodes, max_nodes, runs,shardListPath, step=step))
        #python3 nodescaling 3 2 4 1 

    elif sys.argv[1] == 'inputscaling_d':
        num_shards = int(sys.argv[2])
        min_inputs = int(sys.argv[3])
        max_inputs = int(sys.argv[4])
        num_outputs = int(sys.argv[5])
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_input_scaling(num_shards, min_inputs, max_inputs, num_outputs, runs, defences=True))
    elif sys.argv[1] == 'inputscaling_f':
        num_shards = int(sys.argv[2])
        min_inputs = int(sys.argv[3])
        max_inputs = int(sys.argv[4])
        case = sys.argv[5]
        runs = int(sys.argv[6])
        outfile = sys.argv[7]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_input_scaling(num_shards, min_inputs, max_inputs, runs, case=case))
    
    elif sys.argv[1] == 'clientlatency':
        shards = int(sys.argv[2])
        inputs = int(sys.argv[3])
        outputs = int(sys.argv[4])
        min_batch = int(sys.argv[5])
        max_batch = int(sys.argv[6])
        batch_step = int(sys.argv[7])
        runs = int(sys.argv[8])
        shardListPath = sys.argv[9]
        outfile = sys.argv[10]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_client_latency(shards, inputs, outputs, min_batch, max_batch, batch_step, runs, shardListPath))
        #python tester.py clientlatency 2 2 2 20 20 5 2 test

    elif sys.argv[1] == 'clientlatency_d':
        shards = int(sys.argv[2])
        inputs = int(sys.argv[3])
        outputs = int(sys.argv[4])
        min_batch = int(sys.argv[5])
        max_batch = int(sys.argv[6])
        batch_step = int(sys.argv[7])
        runs = int(sys.argv[8])
        outfile = sys.argv[9]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_client_latency(shards, inputs, outputs, min_batch, max_batch, batch_step, runs, defences=True))
    
    elif sys.argv[1] == 'bano':
        num_shards = int(sys.argv[2])
        runs = int(sys.argv[3])
        shardListPath = sys.argv[4]
        outfile = sys.argv[5]

        n = ChainspaceNetwork(0)
        t = Tester(n, outfile=outfile)

        print (t.measure_bano(num_shards, runs,shardListPath))


    elif sys.argv[1] == 'sharding_measurements':
        min_validators = int(sys.argv[2])
        max_validators = int(sys.argv[3])
#        num_transactions = int(sys.argv[4])
        num_shards = int(sys.argv[4])
        runs = int(sys.argv[5])
        shardListPath = sys.argv[6]
        tpsfile = sys.argv[7]
        latfile = sys.argv[8]
        n = ChainspaceNetwork(0)
        t = Tester(n, tpsfile=tpsfile,latencyfile=latfile)

        print (t.measure_sharding(min_validators, max_validators, num_shards, runs, shardListPath))

    elif sys.argv[1] == 'sharding_measurements12':
        min_validators = int(sys.argv[2])
        max_validators = int(sys.argv[3])
#        num_transactions = int(sys.argv[4])
        num_shards = int(sys.argv[4])
        runs = int(sys.argv[5])
        shardListPath = sys.argv[6]
        tpsfile = sys.argv[7]
        latfile = sys.argv[8]
        n = ChainspaceNetwork(0)
        t = Tester(n, tpsfile=tpsfile,latencyfile=latfile)

        print (t.measure_sharding12(min_validators, max_validators, num_shards, runs, shardListPath))
        duration = 1  # seconds
        freq = 440  # Hz
        os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
        os.system('spd-say "your program has finished"')

    elif sys.argv[1] == 'sharding_measurements1':
        min_validators = int(sys.argv[2])
        max_validators = int(sys.argv[3])
        num_transactions = int(sys.argv[4])
        num_shards = int(sys.argv[5])
        runs = int(sys.argv[6])
        shardListPath = sys.argv[7]
        tpsfile = sys.argv[8]
        latfile = sys.argv[9]
        n = ChainspaceNetwork(0)
        t = Tester(n, tpsfile=tpsfile,latencyfile=latfile)

        print (t.measure_sergi(min_validators, max_validators, num_transactions, num_shards, runs, 4,shardListPath))

