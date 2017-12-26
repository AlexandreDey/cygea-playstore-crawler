import random

with open('dict_sorted','r') as f:
    DICO = f.readlines()
    
print ("Shuffling Dictionary ...")
random.shuffle(DICO)

with open('dict','w') as f:
	for l in DICO:
		f.write(l)

