#
#plotting graph
# Read results files and create a error graph
import numpy as np
import matplotlib.pyplot as plt
import ast
from collections import Counter

mode = 5
minSh = 2
maxSh = 8   # put +1 than you need
minInput = 2
maxInput = 3# put +1 than you need
shardList = [2, 3, 4, 5, 6, 7, 8, 9, 10]

#Clever
filename = "ONE_INPUT/OneInput_"
tpsMean = []
tpsStd  = []
LatMean = []
LatStd  = []
allTps  = x = [[] for i in range(10)]
for i in shardList:
	file = filename+str(i)+".txt"
	f = open(file, "r")
	count = 0
	print(i)
	for line in f:
		if count <=5:
			if count <5:
				line = line.split(" ")
			if count != 4:
				x = ast.literal_eval(line[1])


			if count == 0:   tpsMean.append(x[0]*i) 
			elif count == 1: tpsStd.append(float(line[1]))
			elif count == 2: LatMean.append(x[0])
			elif count == 3: LatStd.append(float(line[1]))
			elif count == 4: pass
			elif count == 5: 
				print(ast.literal_eval(line))
				allTps[i-1].append(ast.literal_eval(line))
			count += 1
#print(allTps)

### Rabdom ###
filename2 = "TWO_INPUT/TWOInput_"
tpsMeanRand = []
tpsStdRand  = []
LatMeanRand = []
LatStdRand  = []
allTpsRand  = x = [[] for i in range(10)]

for i in shardList:
	file = filename2+str(i)+".txt"
	f = open(file, "r")
	count = 0
	for line in f:
		if count <=5:
			if count <5:
				line = line.split(" ")
			if count != 4:
				x = ast.literal_eval(line[1])


			if count == 0:   tpsMeanRand.append(x[0]*i) 
			elif count == 1: tpsStdRand.append(float(line[1]))
			elif count == 2: LatMeanRand.append(x[0])
			elif count == 3: LatStdRand.append(float(line[1]))
			elif count == 4: pass
			elif count == 5: 
				#print(x)
				allTpsRand[i-1].append(ast.literal_eval(line))
			count += 1




file = open("test",'w')

asymetricerrorStd = [tpsStd, tpsStd]

x = shardList
y = tpsMean
fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
ax0.errorbar(x, y, yerr=asymetricerrorStd, fmt='-o', label = "1_Input")
ax0.set_ylabel("Tps")
ax0.set_title("Evolution of the tps and latency in function of the nbr of shards")
ax0.grid(True, which = "both")

ax0.set_title("INPUT PLOT WITH FOUR NODES PER SHARD")

y = LatMean
asymetricerrorLatency = [LatStd, LatStd]
ax1.errorbar(x, y, yerr=asymetricerrorLatency, fmt='-o', label = "1_Input" )
ax1.set_ylabel("Latency[ms]")
ax1.set_xlabel("Number of shards")
ax1.grid(True, which = "both")

file.write("this is input plot")
# Program to calculate moving average using numpy


arr = tpsMean
window_size = 2

i = 0
# Initialize an empty list to store moving averages
moving_averages = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr) - window_size + 1:

	# Calculate the average of current window
	window_average = np.diff(arr[i:i+window_size])
	#i:i+window_size]) / w, 2)
	
	# Store the average of current
	# window in moving average list
	moving_averages.append(window_average)
	
	# Shift window to right by one position
	i += 1
print(tpsMean)

print(moving_averages)
#print(tpsMean)
print(np.mean(tpsMean))
print(np.average(tpsMean))
print(np.mean(moving_averages))
file.write(str(np.mean(moving_averages)))


asymetricerrorStdRand = [tpsStdRand, tpsStdRand]
x = [elem+0.05 for elem in x]
y = tpsMeanRand

ax0.errorbar(x, y, yerr=asymetricerrorStdRand, fmt='-x', label = "2_Inputs")

y = LatMeanRand
asymetricerrorLatencyRand = [LatStdRand, LatStdRand]
ax1.errorbar(x, y, yerr=asymetricerrorLatencyRand, fmt='-x', label = "2_Inputs")

ax0.legend()
ax1.legend()

#plt.savefig("Graph_Clever_Random_NODE_FOUR_INPUTS.png")

# plt.show()




rows = len(shardList)
fig, ax = plt.subplots(rows, 
					   sharex='col',figsize=(10,10))
					   #sharey='row')
#ax[0].set_title("TWO NODES")

ax[0].set_title("Distribution of the tps in function of the number of shard(s) used with FOUR NODES")

for row in range(rows):
	nbr = len(allTps[shardList[row]-1][0])
	y = [0]*nbr
	ax[row].scatter(allTps[shardList[row]-1][0], y, label = '1_Input')
	ax[row].set_ylabel('shard:'+str(shardList[row]))

	
	nbr = len(allTpsRand[shardList[row]-1][0])
	y = [0.5]*nbr	
	ax[row].scatter(allTpsRand[shardList[row]-1][0], y, label = '2_Inputs')
	ax[row].legend()
plt.xlabel("Tps")
#plt.savefig("Graph_distrib_Clever_Random_NODE_FOUR_INPUTS.png")



arr = tpsMean
window_size = 2

i = 0
# Initialize an empty list to store moving averages
moving_averages = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr) - window_size + 1:

	# Calculate the average of current window
	window_average = np.diff(arr[i:i+window_size])
	#i:i+window_size]) / w, 2)
	
	# Store the average of current
	# window in moving average list
	moving_averages.append(window_average)
	
	# Shift window to right by one position
	i += 1
print(tpsMean)

#print(moving_averages)
#print(tpsMean)
print("tpsmean: ",np.mean(tpsMean))
#print(np.average(tpsMean))
print("tps mov average:",np.mean(moving_averages))
#file.write(str(np.mean(moving_averages)))
print("---------------here-----------------------")

arr1 = tpsMeanRand
window_size = 2

i = 0
# Initialize an empty list to store moving averages
moving_averages1 = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr1) - window_size + 1:

	# Calculate the average of current window
	window_average = np.diff(arr1[i:i+window_size])
	#i:i+window_size]) / w, 2)
	
	# Store the average of current
	# window in moving average list
	moving_averages1.append(window_average)
	
	# Shift window to right by one position
	i += 1
print(tpsMeanRand)

#print(moving_averages1)
#print(tpsMeanRand)
print("tpsmeanRandom: ",np.mean(tpsMeanRand))
#print(np.average(tpsMean))
print("tps mov averageRandom:",np.mean(moving_averages1))

#----------------------------
print("----------------------LATENCY------------------------------")

arr2 = LatMean
window_size = 2

i = 0
# Initialize an empty list to store moving averages
moving_averages2 = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr2) - window_size + 1:

	# Calculate the average of current window
	window_average = np.diff(arr2[i:i+window_size])
	#i:i+window_size]) / w, 2)
	
	# Store the average of current
	# window in moving average list
	moving_averages2.append(window_average)
	
	# Shift window to right by one position
	i += 1
print(LatMean)

print(moving_averages2)
#print(tpsMean)
print("latmean: ",np.mean(LatMean))
#print(np.average(tpsMean))
print("tps mov average:",np.mean(moving_averages2))
#file.write(str(np.mean(moving_averages)))
print("--------------------------------------")

arr12 = LatMeanRand
window_size = 2

i = 0
# Initialize an empty list to store moving averages
moving_averages12 = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr12) - window_size + 1:

	# Calculate the average of current window
	window_average = np.diff(arr12[i:i+window_size])
	#i:i+window_size]) / w, 2)
	
	# Store the average of current
	# window in moving average list
	moving_averages12.append(window_average)
	
	# Shift window to right by one position
	i += 1
print(LatMeanRand)

print(moving_averages12)
#print(tpsMeanRand)
print("latmeanrandom: ",np.mean(LatMeanRand))
#print(np.average(tpsMean))
print("lat mov averagerandom:",np.mean(moving_averages12))


