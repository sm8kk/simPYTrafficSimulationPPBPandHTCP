from __future__ import division
from operator import itemgetter
import sys, pdb, csv
import simpy
import random
import math
import numpy as np
import globals as G
"""
Author: Sourav Maji

Software simulates a Poisson Pareto Burst Process

1. A Poisson process is defined where the inter-arrival times of events (i.e, bursts)
are generated from an exponential distribution, say mean burst arrivals are m_burstArrivals /sec
then inter_burst_arrivals = 1.0/m_burstArrivals
inter_arrival_x = exp(inter_burst_arrivals)
#param1: m_burstArrivals

2. The burst lengths are generated from a pareto distribution
A pareto distribution parameters are: m_shape, m_scale
for 1 < m_shape < 2, the distribution has infinite variance, and 
the PPBP demonstrates a long range dependence (LRD) process, which is characterized
by the Hurst parameter m_h. 
If 0 < m_h < 0.5, it is a negatively correlated process
If m_h = 0.5, the subsequent events are not correlated to present or prior events (no-dependency)
If 0.5 < m_h < 1, it is a positively correlated LRD process

m_shape = 3 -2*m_h
Pareto mean = m_burstLength
and 
mean = m_shape * m_scale/(m_shape -1)
or m_scale = (m_shape -1) * mean / m_shape
or m_scale = (m_shape -1) * m_burstLength / m_shape

m_shape = f(m_h)
m_scale = f(m_burstLength, m_shape)

#param2: m_h
#param3: m_burstLength

3. Each individual burst is generated at a constant bit rate (CBR) i.e., r (e.g. 1 Mbps)
#param4: r

4. The end time of the last event generation of this process, which is also the duration, assuming that it starts at 0 sec
#param5: time_end

"""

"""
Implementation:
bursts: (bs1, be1), (bs2, be2), (bs3, be3) ... (bsn, ben) 
       of format (burst1_start_time, burst1_end_time)
            bs2 - bs1, bs3 - bs2 ... from an exponential distribution
            be1 - bs1, be2 - bs2, ... from a pareto distribution

agg_bursts: Sum of the bursts that are in burst_list, depending at times these bursts
                overlap, the rate in that overlapping time is going to be a multiple of r.
       of format (burst_agg_s1, burst_agg_e1, rate)

Finally play out the agg_burst_list
"""



bursts = []
sort_bursts = []
agg_bursts = []

def PPBPgen(env, pipe, m_burstArrivals, m_h, m_burstLength, r, time_end):
  ts = 0
  inter_burst_arrivals = 1.0/m_burstArrivals
  m_shape = (3 - 2*m_h)
  m_scale = ((m_shape - 1) * m_burstLength)/m_shape
  pps = r/(G.MTU*8)
  delta = G.MTU*8/r
  if(m_scale < delta):
    print "Cannot proceed as burst length is too low than link rate packet length ..."
    return;

  while True:
    tLen = (np.random.pareto(m_shape) + 1)*m_scale
    te = ts + tLen
    bursts.append([ts, "s"])
    bursts.append([te, "e"])
    tInt = np.random.exponential(inter_burst_arrivals)
    ts = ts + tInt
    if(ts > time_end):
      break;
  #Now form the aggregate burst list
  #1. Sort the list based on the timestamps
  global sort_bursts
  sort_bursts = sorted(bursts, key = itemgetter(0))
  
  curPkts = 0
  m=0
  for i in range(len(sort_bursts)-1):
    if(sort_bursts[i][1] == "s"):
      m = m + 1
    curPkts = m*pps*(sort_bursts[i+1][0] - sort_bursts[i][0])
    if(sort_bursts[i][0] < time_end):
      agg_bursts.append([sort_bursts[i][0], sort_bursts[i][1], sort_bursts[i+1][0], sort_bursts[i+1][1], m, int(math.ceil(curPkts))])
    if(sort_bursts[i+1][1] == "e"):
      m = m - 1
  
  bgPktDrops = 0
  pktsRx = 0
  prevTm = env.now
  bgStTime = env.now
  for j in range(len(agg_bursts)):
    pkts = agg_bursts[j][5]
    wtTm = 0.0
    if(pkts > 0):
      wtTm = (agg_bursts[j][2] - agg_bursts[j][0])/pkts
    else:
      wtTm = (agg_bursts[j][2] - agg_bursts[j][0]) #assuming no packets or a silence period
      yield env.timeout(wtTm)
    
    #ensure that the traffic does not go beyond link rate
    if(wtTm < G.minWtTm):
      wtTm = G.minWtTm
    #print "pkts,wtTm:" + str(pkts) + "," + str(wtTm)
    
    bgDrops = 0 
    for i in range(pkts):
      #print "pktNum,time:" + str(i+1) + "," + str(env.now) 
      yield env.timeout(wtTm)
      if(G.swBufQ.qsize() < G.swBufSize):
        G.swBufQ.put(-1)
        pipe.put("NIC sent 1 packet of burst bg traffic: " + str(-1) + " at time:" + str(env.now))
        pktsRx = pktsRx + 1
        #print "Dequeue msg sent at time:" + str(env.now)
      else:
        bgDrops = bgDrops + 1
        bgPktDrops = bgPktDrops + 1
      
    #print "PPBP traffic, pkts gen: " + str(pkts) + ", pkts drop: " + str(bgPktDrops) + ", time: " + str(env.now)
    if(pkts > 0):
      print "PPBP,stTime,time,rate,pktsGen,cumPktsRxd,cumPktsDrop:" + str(bgStTime) + "," + str(env.now) + "," + str((pkts - bgDrops)*G.MTU*8/(1000000*(env.now - prevTm))) + "," + str(pkts) + "," + str(pktsRx) + "," + str(bgPktDrops)
    prevTm = env.now

#(env, pipe, m_burstArrivals, m_h, m_burstLength, r, time_end)
