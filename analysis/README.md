# Analysis

## Setup

Install the prism_tracker module into your environment

```
conda create -n "prism" python=3.8
conda activate prism
conda install -c conda-forge cudatoolkit=10.1 cudnn=7.6

python -m pip install -e src
```

## Download data and Prepare datadrive
Create a datadrive folder at your convenience. Make sure to update `src/prism_tracker/config.py`.
```
datadrive = Path('Path / To / Your / Datadrive')
```

In the datadrive, the structure will be
```
datadrive
│
└───pretrained_models
│   └───audio_model.h5
│   └───motion_model.h5
│   └───motion_norm_params.pkl
│  
└───tasks
    └───latte_making
          └───dataset
          │    └───audio
          │    │    └───raw
          │    │    
          │    └───motion
          │    │    └───raw
          │    │  
          │    └───annotation.csv
          │    └───clap_times.csv
          │    └───classes.txt
          │
          └───preprocessed (will be generated)
          └───result (will be generated)
```

Download required files (model + latte_making dataset) from the following links:
- pretrained_models: TBU
- dataset: TBU

