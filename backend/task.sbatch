#!/bin/bash

#SBATCH --job-name=iris
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --gres=gpu:V100:1
#SBATCH --time=2:00:00
#SBATCH --qos=coc-ice
#SBATCH --output=./logs/iris.out
#SBATCH --mail-type=NONE

cd $SLURM_SUBMIT_DIR

module load anaconda3
module load cuda
eval "$(conda shell.bash hook)"
conda activate iris
python3 src/main.py

