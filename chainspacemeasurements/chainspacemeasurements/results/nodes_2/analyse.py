file_name = ""
for i in range(2,11):
	#print(i)
	file_name = "clever"+str(i)+".txt"
	print(file_name)
	file = open(file_name,'x')
