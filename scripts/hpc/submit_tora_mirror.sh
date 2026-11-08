#!/bin/bash
# wear-beyond-juglet 23 (pr-workspace U3): submit the TORA mirror as pre-registered in
# .scratch/wear-beyond-juglet/preregistration-tora-mirror.md (pr-workspace c54d3e3).
# Four models x every set of rounds 1-3, anchor-fixed, paired, 20 draws, each model and set in
# two jobs of 5 seeds (a 10-seed job runs near the 3 h limit). Round 3's whole-pot frame and
# --pot-size are set by u10_juglet_arm.slurm itself. Prints one line per job: round set arm seeds jobid.
#   bash scripts/hpc/submit_tora_mirror.sh            (from the canonical checkout)
set -euo pipefail
T=/data/gpfs/projects/punim2657/TORA
declare -A AD=(
  [untouched]=""
  [pooled]=$T/output/u10_noalign_pooled_31296425_185502/last.ckpt
  [noise_d100]=$T/output/u10_noalign_noise_d100_31343498_010350/last.ckpt
  [worn_d400]=$T/output/u10_noalign_worn_d400_31343495_234404/last.ckpt
)
for A in "${AD[@]}"; do [ -z "$A" ] || [ -f "$A" ] || { echo "missing $A"; exit 1; }; done
sub() {  # round set seeds...
  local R=$1 SET=$2; shift 2
  for ARM in untouched pooled noise_d100 worn_d400; do
    local J
    J=$(ARM=$ARM ADAPTER=${AD[$ARM]} SET=$SET SEEDS="$*" DRAWS=20 ANCHOR_FREE=false PAIRED=1 \
        LABEL=mirror$R sbatch --parsable --job-name="mirror${R}_${ARM}" scripts/hpc/u10_juglet_arm.slurm)
    echo "round$R $SET $ARM seeds[$*] $J"
  done
}
for SET in csc_whole_clean csc_whole_worn csc_whole_coarsev3; do
  sub 1 $SET 1 2 3 4 5; sub 1 $SET 6 7 8 9 10
done
for SET in csc_whole20_clean csc_whole20_worn4 csc_whole20_coarsev3_1 csc_whole20miss_clean csc_whole20miss_worn4; do
  R=2; [[ $SET == *miss* ]] && R=3
  sub $R $SET 3 4 5 6 7; sub $R $SET 8 9 10 11 12
done
