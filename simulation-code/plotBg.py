from __future__ import division
from operator import itemgetter
import sys, pdb, csv
import matplotlib.pyplot as plt
import simpy
import random
import math
import numpy as np

f = open(str(sys.argv[1]), 'r')
lines = f.readlines()
f.close()

X = []
Y = []

for l in lines:
  X.append(float(l.split(":")[1].split(",")[0]))
  Y.append(float(l.split(":")[1].split(",")[1]))

#print X
#print Y


plt.plot(X, Y)
plt.xlabel("time (s)")
plt.ylabel("traffic rate (Mbps)")
plt.grid(True)
plt.savefig("bgRateFromRun.png")
plt.show()

