# Research Code for PrISM-Tracker
![image](https://github.com/cmusmashlab/prism-tracker/assets/12772049/aab22c21-85cd-468e-9e25-9a0539bae993)



This is the research repository for [PrISM-Tracker: A Framework for Multimodal Procedure Tracking Using Wearable Sensors and State Transition Information with User-Driven Handling of Errors and Uncertainty](https://dl.acm.org/doi/pdf/10.1145/3569504), published at IMWUT 2022, Vol. 6, No. 4.

# Repository Structure
- analysis
    - Python-based code to preprocess audio + motion data, apply human activity recognition (HAR), apply our viterbi algorithm, and simulate human-in-the-loop prompting.
- data collection
    - Swift-based code for the iPhone + Apple Watch app we used to collect data. This can be reused to create a new dataset on our framework.
    - Link to the annotation app.

# Reference

[Download the paper here.](https://rikky0611.github.io/resource/paper/prism-tracker_imwut2022_paper.pdf)

```
Riku Arakawa, Hiromu Yakura, Vimal Mollyn, Suzanne Nie, Emma Russell, Dustin Demeo, Haarika Reddy, Alexander Maytin, Bryan Carroll, Jill Fain Lehman, Mayank Goel. 2022. PrISM-Tracker: A Framework for Multimodal Procedure Tracking Using Wearable Sensors and State Transition Information with User-Driven Handling of Errors and Uncertainty. In Proceedings of the ACM on Interactive, Mobile, Wearable, and Ubiquitous Technologies (IMWUT '22). Association for Computing Machinery, New York, NY, USA.
```

```
@article{DBLP:journals/imwut/ArakawaYMNRDRMC22,
  author       = {Riku Arakawa and
                  Hiromu Yakura and
                  Vimal Mollyn and
                  Suzanne Nie and
                  Emma Russell and
                  Dustin P. DeMeo and
                  Haarika A. Reddy and
                  Alexander K. Maytin and
                  Bryan T. Carroll and
                  Jill Fain Lehman and
                  Mayank Goel},
  title        = {PrISM-Tracker: {A} Framework for Multimodal Procedure Tracking Using
                  Wearable Sensors and State Transition Information with User-Driven
                  Handling of Errors and Uncertainty},
  journal      = {Proc. {ACM} Interact. Mob. Wearable Ubiquitous Technol.},
  volume       = {6},
  number       = {4},
  pages        = {156:1--156:27},
  year         = {2022},
  doi          = {10.1145/3569504},
}
```

# License

This repository is published under MIT license.
Please contact innovation@cmu.edu if you would like another license for your use.
