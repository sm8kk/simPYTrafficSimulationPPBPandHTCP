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

T = []
pkts = []
X = []
Y = []

for l in lines:
  T.append(float(l.split(":")[1].split(",")[0]))
  pkts.append(float(l.split(":")[1].split(",")[1]))

for i in range(len(T) -1):
  X.append(T[i+1])
  Y.append(pkts[i+1]*1500*8/(1000000*(T[i+1] - T[i])))

#print X
#print Y


plt.plot(X, Y)
plt.xlabel("time (s)")
plt.ylabel("traffic rate (Mbps)")
plt.grid(True)
plt.savefig("bufferOPRateFromRun.png")
plt.show()

