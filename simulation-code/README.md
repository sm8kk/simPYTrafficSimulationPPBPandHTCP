1. Seems like the switch buf queue is working fine,
  a. Tested with one TCP flow and it transmits packets at NIC rate, and it is also dequeued at NIC rate.
     NIC rates were kept the same, and we don't see any packet drops, which is the expected behavior

  b. Also added a new feature that limits the TCP window (i.e., maximum send and receive window) as
     an integer times the BDP


2. Run program as:
time python multiFlowProcess.py > test-only-bg-ppbp.txt
cat test-only-bg-ppbp.txt | grep PPBP, > ppbp_gen.txt
cat test-only-bg-ppbp.txt | grep buf, > buff_occ.txt

3. Plot the background traffic from run:
python plotBg.py ppbp_gen.txt

4. plot the output traffic rate from run:
python plotOpTraff.py buff_occ.txt
