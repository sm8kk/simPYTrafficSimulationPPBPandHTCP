from __future__ import division
import simpy
import sys
import math
import numpy as np
import numpy.matlib
import globals as G

class tcpFlow:
  
  def __init__(self, flowID, env, pipe, totalDataSz, ssthresh, rtt, btlNckRate, sTime, swQ):
    self.flowID = flowID
    self.totalDataSz = int(totalDataSz/G.MTU)
    self.ssthresh = ssthresh
    self.rtt = rtt
    self.tmToSendCwnd = self.rtt
    self.tmLeftAfterSendCwnd = 0
    self.vRtt = rtt
    self.btlNckRate = btlNckRate
    self.pps = int(self.btlNckRate/(G.MTU*8))
    self.maxWin = int(self.pps*self.rtt) 
    self.sTime = sTime
    #self.curTime = sTime
    #H-TCP parameters
    self.m_alpha = 1
    self.m_beta = 0.5
    self.m_delta = 0
    self.m_deltaL = 1 # keep this as 1 second
    self.m_lastCon = self.sTime
    self.m_minRtt = self.rtt
    self.m_maxRtt = 0 # check if this should be made rtt or not
    self.m_throughput = 0
    self.m_lastThroughput = 0 # make it 1 to avoid DBZ
    self.m_throughputRatio = 0.2 #from H-TCP paper
    self.m_defaultBackoff = 0.5

    self.pipe = pipe
    self.queue = swQ
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

      # Update m_throughput, 
      if(env.now - self.m_lastCon > 0):
        self.m_throughput = self.txCwnd*G.MTU*8/(env.now - self.m_lastCon)

      # Update m_alpha here (every RTT)
      self.m_delta = env.now - self.m_lastCon
      if(self.m_delta <= self.m_deltaL):
        self.m_alpha = 1
      else:
        diff = self.m_delta - self.m_deltaL
        self.m_alpha = (1 + 10*diff + 0.25*(diff*diff))

      self.m_alpha = 2*(1 - self.m_beta)*self.m_alpha
      print "alpha,beta:" + str(self.m_alpha) + "," + str(self.m_beta)

      if(self.m_alpha < 1):
        self.m_alpha = 1
      # alpha is updated

      # update m_minRtt, m_maxRtt
      if(self.vRtt < self.m_minRtt):
        self.m_minRtt = self.vRtt

      if(self.vRtt > self.m_maxRtt):
        self.m_maxRtt = self.vRtt

      #min and max rtt updated

      if(self.cwnd > self.dataToSend):
        self.cwnd = self.dataToSend

      if(self.queue == "primary"):
        qDelay = G.swBufQ.qsize()/G.dQueRate
      if(self.queue == "scavenger"):
        qDelay = G.swBufQ.qsize()/G.dQueRate

      self.tmToSendCwnd = self.rtt + qDelay
      self.maxWin = int(self.pps*self.tmToSendCwnd) #this ensures that packets are not transmitted faster than link rate
      #flow control
      if(self.cwnd > self.maxWin):
        self.cwnd = self.maxWin

      #print "FlowID: " + str(self.flowID) + ",(time: " + str(self.curTime) + ",cwnd: " + str(self.cwnd) + "), total pkts drop: " + str(self.cumPktsDrop) + ", data rx (Pkts): " + str(self.txData) + ", dur (sec): " + str(self.curTime - self.sTime)

      self.pktsDrop = 0
      pktTxTm = 0

      for i in xrange(self.cwnd):
        if(self.queue == "primary"):
          if(G.swBufQ.qsize() < G.swBufSize):
            G.swBufQ.put(self.flowID)
            yield env.timeout(1/self.pps)
            self.pipe.put("NIC sent 1 packet to primary of flowID: " + str(self.flowID))
	  else:
	    self.pktsDrop = self.pktsDrop + 1
            yield env.timeout(1/self.pps)
        elif(self.queue == "scavenger"):
          if(G.swBufQScav.qsize() < G.swBufSize):
            G.swBufQScav.put(self.flowID)
            yield env.timeout(1/self.pps)
            self.pipe.put("NIC sent 1 packet of to scavenger flowID: " + str(self.flowID))
	  else:
	    self.pktsDrop = self.pktsDrop + 1
            yield env.timeout(1/self.pps)
        self.txCwnd = self.cwnd - self.pktsDrop
        pktTxTm = (self.cwnd/self.pps)

      print "FlowID,stTime,time,cwnd,txCwnd,cumPktsRx,cumPktsDrop,maxWin:" + str(self.flowID) + "," + str(self.sTime) + "," + str(env.now) + "," + str(self.cwnd) + "," + str(self.txCwnd) + "," + str(self.txData) + "," + str(self.cumPktsDrop) + "," + str(self.maxWin)

      if(self.queue == "primary"):
        print "Time: " + str(env.now) + ", priBuf occupied: " + str(G.swBufQ.qsize())
      elif(self.queue == "scavenger"):
        print "Time: " + str(env.now) + ", scavBuf occupied: " + str(G.swBufQScav.qsize())
      #adjust window due to packet drop, or congestion control
      #congestion avoidance

      if(self.pktsDrop > 0):
        # Congestion detected, update beta
        self.m_lastCon = env.now
        if(self.m_lastThroughput > 0):
          if(((self.m_throughput - self.m_lastThroughput)/self.m_lastThroughput) > self.m_throughputRatio):
            self.m_beta = self.m_defaultBackoff
          else:
            self.m_beta = self.m_minRtt/self.m_maxRtt
        else:
          self.m_beta = self.m_defaultBackoff
        
        self.cwnd = int(self.m_beta*self.cwnd)
        self.ssthresh = self.cwnd
        #print "FlowID: " + str(self.flowID) + ", Time: " + str(env.now) + ", Pkts dropped: " + str(self.pktsDrop) + ", cwnd: " + str(self.cwnd) + ", ssthresh: " + str(self.ssthresh)
    

      self.txData = self.txData + self.txCwnd #actual amount of data send, without packet drops
      self.cumPktsDrop = self.cumPktsDrop + self.pktsDrop
      self.dataToSend = self.totalDataSz - self.txData
      #self.curTime = self.curTime + self.rtt

      #for slow start
      if(self.cwnd < self.ssthresh):
        #the flow is in slow start, double cwnd every rtt
        self.cwnd = 2*self.cwnd
      else:
        # update cwnd
        cwAdd = ((G.MTU*G.MTU) + self.cwnd*G.MTU*self.m_alpha)/(self.cwnd*G.MTU)
        cwAdd = int(numpy.max([1, cwAdd]))
        self.cwnd = self.cwnd + cwAdd
        print "congestion avoidance, updated cwnd:" + str(self.cwnd)
    
      self.vRtt = self.rtt + qDelay
      if (self.tmToSendCwnd - pktTxTm > 0):
        yield env.timeout(self.tmToSendCwnd - pktTxTm)

      self.pipe.put("Start signal sent by flow : " + str(self.flowID))
