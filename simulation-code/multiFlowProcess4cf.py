from __future__ import division
import sys, pdb, csv
import simpy
import Queue
import random
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
      print "priBuf,time,pkts_deq:" + str(env.now) + "," + str(pktsDeq)
    
    #dequeue the scavenger queue only when there is no packet in the
    #primary queue
    while(G.swBufQ.qsize() < 1):
      if(G.swBufQScav.qsize() > 0):
        pktsDeqSc = 0
        G.swBufQScav.get()
        pktsDeqSc = pktsDeqSc + 1
        yield env.timeout(1/G.dQueRate)
        print "scavBuf,time,pkts_deq:" + str(env.now) + "," + str(pktsDeqSc)
      else:
        break;

#def tcpFlowSources(env, numFlows, intervalMean, rttMean):
def tcpFlowSources(env, Rthresh):
  #time to fill the switch buffer, for a 5MB buffer T = 40ms
  T = (G.swBufSizeBytes*8)/G.dQueRateBps
  flowID = 1 #C1
  rtt = 0.10 #100ms
  tcpRate = 800000000# 1 Gbps
  swQ = "primary" #send first flow to primary queue
  #as rtt > T
  if(G.maxWinBDP*tcpRate > Rthresh):
    swQ = "scavenger"
  # TCP flow param: self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " and rate: " + str(tcpRate) + " at time: " + str(env.now)
  f = TCP.tcpFlow(flowID, env, pipe, 20*10**9, G.ssthresh, rtt, tcpRate, env.now, swQ)
  t = 0
  yield env.timeout(t)

  #C21
  flowID = 21 #C21
  rtt = 0.10 #100ms
  tcpRate = 300000000 #300 Mbps
  swQ = "primary" #send first flow to primary queue
  if(G.maxWinBDP*tcpRate > Rthresh):
    swQ = "scavenger"
  # TCP flow param: self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " and rate: " + str(tcpRate) + " at time: " + str(env.now)
  f = TCP.tcpFlow(flowID, env, pipe, 20*10**9, G.ssthresh, rtt, tcpRate, env.now, swQ)
  t = 0
  yield env.timeout(t)

  #C22
  flowID = 22 #C22
  rtt = 0.10 #100ms
  tcpRate = 200000000 #300 Mbps
  swQ = "primary" #send first flow to primary queue
  if(G.maxWinBDP*tcpRate > Rthresh):
    swQ = "scavenger"
  # TCP flow param: self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " and rate: " + str(tcpRate) + " at time: " + str(env.now)
  f = TCP.tcpFlow(flowID, env, pipe, 20*10**9, G.ssthresh, rtt, tcpRate, env.now, swQ)
  t = 0
  yield env.timeout(t)

  #C3
  flowID = 3 #C3
  rtt = 0.01 #10ms
  tcpRate = 800000000 #1 Gbps
  swQ = "primary" #send first flow to primary queue
  if(G.maxWinBDP*tcpRate > Rthresh):
    swQ = "scavenger"
  # TCP flow param: self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime
  print "New TCP flow (flowID: " + str(flowID) + ") with RTT: " + str(rtt) + " and rate: " + str(tcpRate) + " at time: " + str(env.now)
  f = TCP.tcpFlow(flowID, env, pipe, 20*10**9, G.ssthresh, rtt, tcpRate, env.now, swQ)
  t = 0
  yield env.timeout(t)


Rthresh = float(sys.argv[1])

env = simpy.Environment()
pipe = simpy.Store(env)
Q = env.process(dequeueBuf(env, pipe))

#env.process(burstProc.PPBPgen(env, pipe, G.m_burstArrivals, G.m_h, G.m_burstLength, G.cbr, G.runTime))
#env.process(tcpFlowSources(env, G.numFlows, G.intervalMean, G.rttMean))
env.process(tcpFlowSources(env, Rthresh))

env.run(until=G.runTime)
