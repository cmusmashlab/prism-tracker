# Analysis

## Setup

Install the prism_tracker module into your environment

```
$ conda create -n "prism" python=3.8
$ conda activate prism
$ conda install -c conda-forge cudatoolkit=10.1 cudnn=7.6
```

## Download data and Prepare datadrive
Create a datadrive folder at your convenience. Make sure to update `src/prism_tracker/config.py`.
```
datadrive = Path('Path / To / Your / Datadrive')
```
After that, please run
```
$ python -m pip install -e src
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
```

Download the required files from the following links:
- pretrained_models: https://www.dropbox.com/sh/w3lo0f1k6w90b5w/AADuoDVSKuY9kQSPx2RRGJ_Ma?dl=0
- dataset: https://www.dropbox.com/sh/93jd6elugxgvm6k/AACL3XGiP8-UXPKIWK-h9Ud1a?dl=0
    - latte-making and cooking tasks are available

**You can also create your own dataset by [our data collection app](https://github.com/cmusmashlab/prism-tracker/tree/main/data_collection/SensorLogger).
Please get in touch with us (rarakawa@cs.cmu.edu) for more details.**

## Preprocess
In the `noteobook` directory, run
```
$ python preprocess.py
```

## Run tracking
Follow `notebook/latte_making.ipynb`

