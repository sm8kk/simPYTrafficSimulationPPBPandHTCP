
Data_Dir="/scratch/sm8kk/EF-sim-data/cfRateBurstiness/100ms"
Prog_Dir="/sfs/nfs/blue/sm8kk/simulation-code"
Prog_Name=$Prog_Dir/multiFlowProcess.py

testCaseFile=$1
#Start with 30 runs for each case
N=3
jobNumLim=1

Log_Slurm_Dir=$Data_Dir/slurm_logs
Script_Slurm_Dir=$Prog_Dir/slurm_scripts

mkdir -p $Log_Slurm_Dir
mkdir -p $Script_Slurm_Dir


#create a file to vary the tcp rate, and keep the same level of burstiness, say 1.5
rtt="0.1"

while read testCase
do
    m_burstArrivals=`echo $testCase | awk 'BEGIN {FS = ","} ; { print $1}'`
    cbr=`echo $testCase | awk 'BEGIN {FS = ","} ; { print $2}'`
    rate=`echo $testCase | awk 'BEGIN {FS = ","} ; { print $3}'`
    for i in `seq 1 $N`; do
      prefix=$i"_run_"$rate"_tcpRt_"$m_burstArrivals"_burstArr_"$cbr"_cbr"
      OFILE=$Log_Slurm_Dir/${prefix}.qout
      EFILE=$Log_Slurm_Dir/${prefix}.qerr
      SLURM_SCRIPT=$Script_Slurm_Dir/${prefix}.qpbs

      logFile=$prefix"_log.txt"
      CMD='stdbuf -o0 -e0 time python '$Prog_Name' '$rtt' '$rate' '$m_burstArrivals' '$cbr' '$i' > '$Data_Dir/$logFile
      echo $CMD
      rm ${SLURM_SCRIPT}
      echo "#!/bin/sh" > ${SLURM_SCRIPT}
      echo '#SBATCH -N 1' >> ${SLURM_SCRIPT}
      echo '#SBATCH --ntasks-per-node=1' >> ${SLURM_SCRIPT}
      echo '#SBATCH -t 10:00:00' >> ${SLURM_SCRIPT}
      echo '#SBATCH -p standard' >> ${SLURM_SCRIPT}
      echo '#SBATCH -A hntes_group' >> ${SLURM_SCRIPT}
      echo '#SBATCH --mem=6000' >> ${SLURM_SCRIPT}
      echo '#SBATCH -o "'${OFILE}'"' >> ${SLURM_SCRIPT}
      echo '#SBATCH -e "'${EFILE}'"' >> ${SLURM_SCRIPT}
      echo 'module load anaconda2' >> ${SLURM_SCRIPT}
      echo ${CMD} >> ${SLURM_SCRIPT}
      sbatch ${SLURM_SCRIPT}
      jobs=`squeue -u sm8kk | wc -l`
      echo "Jobs running: $jobs"
      while [ $jobNumLim -lt $jobs ]
      do
        echo "Sleeping for 3 secs ..."
        sleep 3
        jobs=`squeue -u sm8kk | wc -l`
      done
    done
done < $testCaseFile
