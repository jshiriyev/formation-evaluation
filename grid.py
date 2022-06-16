import re

import matplotlib.pyplot as plt

import numpy as np

Nx,Ny,Nz = (1,1,2)

Nsurf_nodes = (Nx+1)*(Ny+1)

coord = np.empty((Nsurf_nodes*6,))
zcorn = np.empty((2*Nx*2*Ny*2*Nz,))

comment = None
endsection = "/"

headers = ["COORD","ZCORN"]
running = [coord,zcorn]

running_temp = []

def starsplit0(string):
	row = string.split("*",maxsplit=2)
	[row.insert(0,"") for _ in range(2-len(row))]
	if len(row[0])==0:
		return 1
	else:
		return int(row[0])

def starsplit1(string):
	row = string.split("*",maxsplit=2)
	[row.insert(0,"") for _ in range(2-len(row))]
	return float(row[1])

splitting0 = np.vectorize(starsplit0)
splitting1 = np.vectorize(starsplit1)

with open("grid.grdecl","r") as text:

	array = []
	
	for line in text:

		line = line.split('\n')[0].strip()

		if line=="":
			continue

		if comment is not None:
			if line[:len(comment)] == comment:
				continue

		line = re.sub(' +',',',line)
		
		row = line.split(",")

		try:
			index = line.index(endsection)
		except ValueError:
			[array.append(col) for col in row]
		else:
			[array.append(col) for col in row[:index]]
			running_temp.append(array)
			array = []
			[array.append(col) for col in row[index+1:]]

for array in running_temp:
	
	section_keyword = array.pop(0)
	index = headers.index(section_keyword)
	
	ints = splitting0(array)
	flts = splitting1(array)

	running[index] = np.repeat(flts,ints)

coord = running[0].reshape((Nsurf_nodes,6))

zcorn = running[1] #((2*Nx*2*Ny*2*Nz,))

print(coord)
print(zcorn)

coord1 = coord*1
coord2 = coord*1

coord1[:,2] = zcorn[ :Nsurf_nodes]
coord1[:,5] = zcorn[  Nsurf_nodes:2*Nsurf_nodes]

coord2[:,2] = zcorn[2*Nsurf_nodes:3*Nsurf_nodes]
coord2[:,5] = zcorn[3*Nsurf_nodes:]
            
fig = plt.figure(figsize=(8,8))

ax = fig.add_subplot(projection='3d')

ax.scatter(*coord1[:,:3].T)
ax.scatter(*coord1[:,3:].T)
ax.scatter(*coord2[:,:3].T)
ax.scatter(*coord2[:,3:].T)

ax.set_xlabel("x-axis")
ax.set_ylabel("y-axis")
ax.set_zlabel("z-axis")

plt.show()
