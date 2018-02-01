from __future__ import division
import sys, pdb, csv
import simpy
import Queue
import random
import numpy as np
import globals as G
#import tcpModel as TCP
import htcpModel as TCP
import ppbp as burstProc


def dequeueBuf(env, pipe):
  while True:
    msg = yield pipe.get()
    #print "Time: " + str(env.now) + "Buf size: " + str(G.swBufQ.qsize()) +", MsgRx: " + msg 
    #dequeue as long as there are packets
    while(G.swBufQ.qsize() > 0):
      pktsDeq = 0
      G.swBufQ.get()
      pktsDeq = pktsDeq + 1
      #dequeue 1 packet every 1/G.dQueRate sec
      yield env.timeout(1/G.dQueRate)
      #print "priBuf,time,pkts_deq:" + str(env.now) + "," + str(pktsDeq)
    
    #dequeue the scavenger queue only when there is no packet in the
    #primary queue
    while(G.swBufQ.qsize() < 1):
      if(G.swBufQScav.qsize() > 0):
        pktsDeqSc = 0
        G.swBufQScav.get()
        pktsDeqSc = pktsDeqSc + 1
        yield env.timeout(1/G.dQueRate)
        #print "scavBuf,time,pkts_deq:" + str(env.now) + "," + str(pktsDeqSc)
      else:
        break;

#def tcpFlowSources(env, numFlows, intervalMean, rttMean):
def tcpFlowSources(env, rtt, tcpRate):
  #generates TCP flow sources at random start times
  #The inter-arrival times are taken from an exponential distribution
  #for i in range(numFlows):
    #rtt = random.expovariate(1/rttMean)
    #t = random.expovariate(1/intervalMean)
    #flowID = i + 1
    # hardcode TCP parameters, for one on one runs
  #rtt = 0.10 #100ms
  flowID = 1
  # TCP flow param: self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " and rate: " + str(tcpRate) + " at time: " + str(env.now)
  swQ = "primary" #send first flow to primary queue
  f = TCP.tcpFlow(flowID, env, pipe, 2000*10**9, G.ssthresh, rtt, tcpRate, env.now, swQ) #send a large 2000GB of data (62.5GB at 1Gbps for 500sec) 
  t = 0
  yield env.timeout(t)
  #For now just send TCP flow and background traffic to the primary queue, and study the effects of
  #different types of cheetah flows

  """
  rtt = 0.20 #200ms
  flowID = 2
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " at time: " + str(env.now)
  swQ = "scavenger" #send second flow to scavenger queue
  f = TCP.tcpFlow(flowID, env, pipe, 2*10**9, G.ssthresh, rtt, G.tcpNICRate, env.now, swQ)
  #yield env.timeout(t)
  """


rtt = float(sys.argv[1])
tcpRate = float(sys.argv[2])
G.m_burstArrivals = float(sys.argv[3])
G.cbr = float(sys.argv[4])
SEED = int(sys.argv[5])

np.random.seed(SEED)
env = simpy.Environment()
pipe = simpy.Store(env)
Q = env.process(dequeueBuf(env, pipe))

env.process(burstProc.PPBPgen(env, pipe, G.m_burstArrivals, G.m_h, G.m_burstLength, G.cbr, G.runTime))
#env.process(tcpFlowSources(env, G.numFlows, G.intervalMean, G.rttMean))
env.process(tcpFlowSources(env, rtt, tcpRate))

env.run(until=G.runTime)
