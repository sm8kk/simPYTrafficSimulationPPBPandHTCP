from __future__ import division
import Queue
# Create a queue or switch port buffer swBuf [] using a bounded list (say 100 packets)
# implement a simple queue, where all packet sizes are the same say, 1500B, and the packets
# in the queue are named as according to the flowID i.e. [1,1,1,1,2,2,2,2,3,3,3,1,1,..]
# packets are removed from the head of the queue at a constant rate, and consequtive packets are 
# added at the end of the queue.
MTU = 1500
swBufSizeBytes = 5*10**6 # a 5 MB buffer
dQueRateBps = 10**9 #link rate in bps, i.e., 1 Gbps
bgNICRate = 10**9 # the maximum traffic rate of the background traffic
swBufQ = Queue.Queue()
swBufQScav = Queue.Queue()

#Cheetah flow params
maxWinBDP = 1 #maximum window is 2 times the BDP
ssthresh = 100000 #100 K packets which is 15 MB, keep it large
tcpNICRate = 10**9 #700 Mbps assuming tc pacing of packets


runTime = 3000 #Change runTime to TCP flow duration, do not use file size
#numFlows = 1
#intervalMean = 5
#rttMean = 0.05 #50ms being the average rtt

transient = 0
m_burstArrivals = 100 # 100 bursts per second
m_h = 0.5 # keep Hurst parameter > 0.5 for LRD
m_burstLength = 0.1 # 100 ms as the mean burst size
cbr = 10**6 # 1 Mbps constant bit rate


#minimum waiting time for a packet
minWtTm = (MTU*8)/bgNICRate

#size and rate in pkts
swBufSize = int(swBufSizeBytes/MTU)
dQueRate = int(dQueRateBps/(MTU*8)) # 83333 pps for a 1 Gbps link rate
