# FCS computer
#
# Input: bitstring to be FCSd (100011011000110101...)
# Output: FCS on stdout
#
# Provided functions:
#   Fcs_list(list)
#      - input:  list of ones and zeroes (ie [1,0,1,0,0,1])
#      - output: FCS in list format
#   Fcs_bitstring(str)
#      - input:  array of ones and zeroes (ie 101001)
#      - output  FCS in array format
# Usage:
#   $ python fcs.py "1010001010100101011100010101111100..."

import sys,os

# Compute FCS with I/O in LIST
def Fcs_list(dlist):
	#print(dlist)
	# Get len to be complemented
	if len(dlist) < 32:
		dinvlen=len(dlist)
	else:
		dinvlen=32

	# Complement it
	#print(dlist[0:dinvlen])
	for i in range (0,dinvlen):
		if dlist[i] == '0':
			dlist[i]='1'
		else:
			dlist[i]='0'
	#print(dlist[0:dinvlen])

	# Prepare result
	fcs=[]
	res=[]
	for i in range(0,32):
		fcs.append(0)
		res.append(0)

	# Compute FCS
	for i in range(0,len(dlist)):
		if dlist[i] == '1':
			xr=1^fcs[31]
		else:
			xr=0^fcs[31]

		fcs[31]=fcs[30]
		fcs[30]=fcs[29]
		fcs[29]=fcs[28]
		fcs[28]=fcs[27]
		fcs[27]=fcs[26]
		fcs[26]=fcs[25]^xr
		fcs[25]=fcs[24]
		fcs[24]=fcs[23]
		fcs[23]=fcs[22]^xr
		fcs[22]=fcs[21]^xr
		fcs[21]=fcs[20]
		fcs[20]=fcs[19]
		fcs[19]=fcs[18]
		fcs[18]=fcs[17]
		fcs[17]=fcs[16]
		fcs[16]=fcs[15]^xr
		fcs[15]=fcs[14]
		fcs[14]=fcs[13]
		fcs[13]=fcs[12]
		fcs[12]=fcs[11]^xr
		fcs[11]=fcs[10]^xr
		fcs[10]=fcs[9]^xr
		fcs[9]=fcs[8]
		fcs[8]=fcs[7]^xr
		fcs[7]=fcs[6]^xr
		fcs[6]=fcs[5]
		fcs[5]=fcs[4]^xr
		fcs[4]=fcs[3]^xr
		fcs[3]=fcs[2]
		fcs[2]=fcs[1]^xr
		fcs[1]=fcs[0]^xr
		fcs[0]=xr

	# Complement back
	for i in range(0,32):
		if fcs[i] == 1:
			res[31-i]=0
		else:
			res[31-i]=1
	return res
# END of Fcs_list()

# Compute FCS with I/O in ARRAY (C char*)
def Fcs_bitstring(data):

	dlist=[]

	# Convert bitstring to list
	for i in data[:]:
		dlist.append(i)

	res=Fcs_list(dlist)
	# Ress as result in string format
	ress=""
	for i in range(1,32):
		ress+=`res[i]`
	ress+=`res[0]`

	return ress
# END of Fcs_bitstring

# Demo
if __name__ == '__main__':
    import sys
    data=sys.argv[1]
    print(Fcs_bitstring(data))
