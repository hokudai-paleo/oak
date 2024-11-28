# oak: Automated curation software for large-scale tomographic images

## Prerequisites
- Mac mini cluster (https://github.com/hokudai-paleo/macmini-cluster/wiki)

## How to install
### Python virtual env with conda
```
conda create -n oak python=3.9
conda activate oak
conda install requests
conda install pyqt
conda install numpy
conda install mpi4py
conda install -c conda-forge mpi4py openmpi
conda install openpxl
conda install PyPDF2
conda install typing_extensions
conda install reportlab
conda install pdf2image
conda deactivate
```
### install other tools
```
brew install ffmpeg
brew install poppler
```

## How to run
```
cd (directory-of-oak)
mpirun -np (proc num) -hostfile (PATH-to-hostfile) /Users/(username)/.pyenv/versions/miniforge3/envs/oak/bin/python3 main.py
```
