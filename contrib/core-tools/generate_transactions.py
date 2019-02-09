
# This script generates a file "test_transactions.txt" containing
# transactions to test. This file is used by the client to submit
# transactions from a file for testing purposes. Files have format:
# <transaction ID>\t<input1;input2;input3>\t<output1;output2;output3;output4>
# is fixed to 0 (meaning ACTIVE)

# Bano / 01Feb2019
# ==================
import random
import sys

# FIXME: How many shards
numShards=4

# FIXME: How many transactions
numTransactions=100

# FIXME: How many inputs per transaction
numInputs=2

# FIXME: How many outputs per transaction
numOutputs=2

# FIXME: Path where to write the output files
path = "/Users/sheharbano/Projects/blockchain/byzcuit/chainspacecore/ChainSpaceClientConfig/"

# FIXME: Used to seed output object generator
# Choose a large number, greater than the input objects generated
# to avoid overwriting input objects
outputObjectCounterIndex=1000000000

# This is indexed by shard ID and value represents the next
# unused output object in this shard
outputObjectCounter = []

# FIXME: Used to seed transaction ID generator
transactionIDCounter=1


# This is indexed by shard ID and value represents the next
# unused (=active) object in this shard
inputObjectCounter = []

# Mode 0: means that input objects will be chosen from random shards
# Mode 1: means that input objects will be sequentially chosen from shards in round robin
inputObjectMode = 0


# Mode 0: means that output objects will be chosen from random shards
# Mode 1: means that output objects will be sequentially chosen from shards in round robin
# Mode -1: means that numDummyObjects (= non-input shards) will be added to transaction; (assuming createDummyObjects = 1)
outputObjectMode = -1

# Used in getNextShard to get shards sequentially
nextShardCounter = 1

# The set of shard IDs
allShards = set()

# Dummy objects on (1) or off (0)
# If this is on, will add to the transaction input/output object pair(s) from the non-input shards
createDummyObjects = 1

# How many dummy objects to add (assuming outputObjectMode has been set to -1)
# a positive integer X means add 0 to X dummy objects, depending on the number of non-input shards
# -1 means will add as many dummy objects as there are non-input shards
numDummyObjects = 2

def config(newNumShards, newNumTransactions, newNumInputs, newNumOutputs, newPath, newInputObjectMode, newCreateDummyObjects, newNumDummyObjects, newOutputObjectMode):
	global numShards
	global numTransactions
	global numInputs
	global numOutputs
	global path
	global inputObjectMode
	global createDummyObjects
	global numDummyObjects
	global outputObjectMode
	numShards = newNumShards
	numTransactions = newNumTransactions
	numInputs = newNumInputs
	numOutputs = newNumOutputs
	path = newPath
	inputObjectMode = newInputObjectMode
	createDummyObjects = newCreateDummyObjects
	numDummyObjects = newNumDummyObjects
	outputObjectMode = newOutputObjectMode

def initAllShards():
	global numShards
	for i in range(0,numShards):
		allShards.add(i)

def initInputObjectCounter():
	global numShards
	global inputObjectCounter
	inputObjectCounter = [None] * numShards
	#inputObjectCounter[0] = numShards # special case, since shards start from 0

	for i in range(0,numShards):
		inputObjectCounter[i] = i

def initOutputObjectCounter():
	global numShards
	global outputObjectCounter
	outputObjectCounter = [None] * numShards

	for i in range(0,numShards):
		outputObjectCounter[i] = outputObjectCounterIndex + i

def getNextInputObject(shardID):
	global inputObjectCounter
	nextObject = inputObjectCounter[shardID]
	inputObjectCounter[shardID] += numShards
	return nextObject

def getNextOutputObject(shardID):
	global outputObjectCounter
	nextObject = outputObjectCounter[shardID]
	outputObjectCounter[shardID] += numShards
	return nextObject

def getNextOutputObjectSequential():
	global outputObjectCounterIndex
	nextObject = outputObjectCounterIndex
	outputObjectCounterIndex += 1
	return nextObject

def getNextTransactionID():
	global transactionIDCounter
	nextID = transactionIDCounter
	transactionIDCounter += 1
	return nextID

def mapObjectToShard(theObject):
	# This is how Byzcuit maps objects to shards
	return theObject % numShards


def getRandomShard():
	return random.randint(0,numShards-1)


def getNextShard():
	global nextShardCounter
	global numShards
	nextShard = nextShardCounter % numShards
	nextShardCounter += 1
	return nextShard

def genTransactionFile():
	# Initialise the set of all shard IDs
	initAllShards()

	# Initialise input and output object counters
	initInputObjectCounter()
	initOutputObjectCounter()

	inputShards = set()
	outputShards = set()

	# Create / open file to write
	fileName = path+"test_transactions.txt"
	outFile = open(fileName, "w")

	# Write objects and their status to corresponding files
	for i in range(numTransactions):

		transactionID = getNextTransactionID()

		# Generate inputs (chosen from random shards)
		inputs = ""
		for j in range(numInputs):
			delimiter = ";"
			# don't put delimiter after the last input
			if j == numInputs-1:
				delimiter = ""

			if inputObjectMode == 0:
				inputShard = getRandomShard()
			else:
				inputShard = getNextShard()

			inputs = inputs + str(getNextInputObject(inputShard)) + delimiter
			inputShards.add(inputShard)


		# generate output objects
        	outputs = ""

		if outputObjectMode != -1: # generate output objects randomly or sequentially
			for j in range(numOutputs):
				delimiter = ";"
				#don't put delimiter after the last output
				if j == numOutputs-1:
					delimiter = ""

				strOutput = ""

                		# 0 for random output selection, and 1 for sequential
				if outputObjectMode == 0:
					outputShard = getRandomShard()
					strOutput = str(getNextOutputObject(outputShard))
				else:
					theObject = getNextOutputObjectSequential()
					strOutput = str(theObject)
					outputShard = mapObjectToShard(theObject)

				outputShards.add(outputShard)
				outputs = outputs + strOutput + delimiter

                	if createDummyObjects == 1:
                    		outputOnlyShards = outputShards - inputShards # shards that only occur in output

                    		# Include dummy objects from all the outputOnly shards
                    		counter = 0
                    		for eachShard in outputOnlyShards: # add dummy objects to inputs for output-only shards
                        		counter += 1
                        		inputObject = getNextInputObject(eachShard)
                        		inputs = inputs + ";" + str(inputObject)

                # Bano: This is old code that used to sequentially pick outputs from shards
		#	for k in range(numOutputs):
		#		delimiter = ";"
		#		# don't put delimiter after the last output
		#		if k == numOutputs-1:
		#			delimiter = ""
                #
		#		outputs = outputs + str(getNextOutputObjectSequential()) + delimiter
            	#
		#	endOfLine = "\n"
		#	if i == numTransactions-1:
		#		endOfLine = ""
            	#
		#	line = str(transactionID) + "\t" + inputs + "\t" + outputs + endOfLine

		# add all or up to numDummyObjects non-input shards to the output
		else: #createDummyObjects is implicitly assumed to be true in this case
			nonInputShards = allShards - inputShards

			# Include dummy objects from all the non-input shards
			counter = 0
			for eachShard in nonInputShards:
				counter += 1

				outputObject = getNextOutputObjectSequential()
				while mapObjectToShard(outputObject) != eachShard:
					outputObject = getNextOutputObjectSequential()

				inputObject = getNextInputObject(eachShard)
				inputs = inputs + ";" + str(inputObject)

				delimiter = ";"
				# don't put delimiter after the last output
				if counter == len(nonInputShards):
					delimiter = ""
				outputs = outputs + str(outputObject) + delimiter

				if counter == numDummyObjects:
					break

		endOfLine = "\n"
		if i == numTransactions-1:
			endOfLine = ""

		line = str(transactionID) + "\t" + inputs + "\t" + outputs + endOfLine

		outFile.write(line)

		inputShards.clear()
		outputShards.clear()

	# Close file
	outFile.close()

# =============
# Program entry point
# =============
if __name__ == '__main__':
	if len(sys.argv) > 1:
		config(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9]))
	genTransactionFile()
