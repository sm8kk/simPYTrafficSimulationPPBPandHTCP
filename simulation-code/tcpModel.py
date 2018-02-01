from __future__ import division
import simpy
import sys
import numpy as np
import numpy.matlib
import globals as G

class tcpFlow:
  
  def __init__(self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime):
    self.flowID = flowID
    self.totalDataSz = int(totalDataSz/G.MTU)
    self.ssthresh = ssthresh
    self.rtt = rtt
    self.tmToSendCwnd = self.rtt
    self.tmLeftAfterSendCwnd = 0
    self.btlNckRate = btlNckRate
    self.pps = int(self.btlNckRate/(G.MTU*8))
    self.maxWin = int(self.pps*self.rtt) 
    self.sTime = sTime
    #self.curTime = sTime
    self.pipe = pipe
    self.cwnd = 1
    self.txCwnd = 0
    self.txData = 0
    self.pktsDrop = 0
    self.cumPktsDrop = 0
    self.dataToSend = self.totalDataSz - self.txData + self.cumPktsDrop
    self.process = env.process(self.processFlow(env))
   
  def processFlow(self, env):
    #for i in range(1000):
    #Execute in a loop as long as there is data to send
    while(self.dataToSend >= 1):
      if(self.dataToSend < 1):
        return;

      if(self.cwnd > self.dataToSend):
        self.cwnd = self.dataToSend

      #print "FlowID: " + str(self.flowID) + ",(time: " + str(self.curTime) + ",cwnd: " + str(self.cwnd) + "), total pkts drop: " + str(self.cumPktsDrop) + ", data rx (Pkts): " + str(self.txData) + ", dur (sec): " + str(self.curTime - self.sTime)

      qDelay = G.swBufQ.qsize()/G.dQueRate
      self.tmToSendCwnd = self.rtt + qDelay
      self.maxWin = int(self.pps*self.tmToSendCwnd) #this ensures that packets are not transmitted faster than link rate

      if(self.cwnd > self.maxWin):
        self.cwnd = self.maxWin
 
      self.pktsDrop = 0
      pktTxTm = 0
      for i in xrange(self.cwnd):
        if(G.swBufQ.qsize() < G.swBufSize):
          G.swBufQ.put(self.flowID)
          yield env.timeout(1/self.pps)
          self.pipe.put("NIC sent 1 packet of flowID: " + str(self.flowID))
	else:
	  self.pktsDrop = self.pktsDrop + 1
          yield env.timeout(1/self.pps)

      self.txCwnd = self.cwnd - self.pktsDrop
      pktTxTm = (self.cwnd/self.pps)

      print "FlowID,time,cwnd,txCwnd,cumPktsDrop,maxWin:" + str(self.flowID) + "," + str(env.now) + "," + str(self.cwnd) + "," + str(self.txCwnd) + "," + str(self.cumPktsDrop) + "," + str(self.maxWin)

      print "Time: " + str(env.now) + ", Buf occupied: " + str(G.swBufQ.qsize())
      #adjust window due to packet drop, or congestion control
      if(self.pktsDrop > 0):
        self.cwnd = int(self.cwnd/2)
        self.ssthresh = self.cwnd
        #print "FlowID: " + str(self.flowID) + ", Time: " + str(env.now) + ", Pkts dropped: " + str(self.pktsDrop) + ", cwnd: " + str(self.cwnd) + ", ssthresh: " + str(self.ssthresh)
    

      self.txData = self.txData + self.txCwnd #actual amount of data send, without packet drops
      self.cumPktsDrop = self.cumPktsDrop + self.pktsDrop
      self.dataToSend = self.totalDataSz - self.txData
      #self.curTime = self.curTime + self.rtt


      if(self.cwnd < self.ssthresh):
        #the flow is in slow start, double cwnd every rtt
        self.cwnd = 2*self.cwnd
      else:
        #congestion avoidance
        self.cwnd = self.cwnd + 1
    
      if (self.tmToSendCwnd - pktTxTm > 0):
        yield env.timeout(self.tmToSendCwnd - pktTxTm)

      self.pipe.put("Start signal sent by flow : " + str(self.flowID))
