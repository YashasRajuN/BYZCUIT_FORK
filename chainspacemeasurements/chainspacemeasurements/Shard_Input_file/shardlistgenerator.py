import random

nbrTrans = 46000
#nbrTrans = 10
file = open("shards_clever2.txt", "w")
shards = 1
print(int(nbrTrans/shards))

k = int(nbrTrans/shards)
print(k)

for i in range(k):
	for j in range(0,shards+1):
	#a = str(random.randint(0,9))
	#b = str(random.randint(0,9))
	
		a = str(j)
		b = str(j)
		c = a + "," + b
		#print(c)
		file.write(c)
		file.write("\n")
file.close()
