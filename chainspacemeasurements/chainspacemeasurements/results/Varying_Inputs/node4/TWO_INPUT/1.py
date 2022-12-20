#

Dir = "/home/yash/chainspace/chainspacemeasurements/chainspacemeasurements/results/nodes_4/random/"
for i in range(2,11):
	file_name1 = "TWOInput_"+str(i)+".txt"
	file_name2 = str(Dir)+"random"+str(i)+".txt"
	with open(file_name2,'r') as firstfile, open(file_name1,'w') as secondfile:
		for line in firstfile:
			secondfile.write(line)
