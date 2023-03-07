import os

import numpy as np
import pandas as pd


def load_annotations_dict(path_to_original):
    """
    load annotations for the espresso task
    """
    userdfs = dict()
    espresso = path_to_original / "espresso.csv"
    df = pd.read_csv(str(espresso))

    # fill NaNs with last seen values -> results in the participant id being
    # filled
    df.ffill(inplace=True)  # fill participant

    for user in df["Participant"].unique():
        userdf = df.loc[df['Participant'] == user]
        userdf.reset_index(drop=True)
        userdfs[user] = userdf
    return userdfs


def check_processed(path_to_processed):
    """
    Check which PIDs are already processed
    """
    processed = []
    for filename in sorted(os.listdir(path_to_processed)):
        pid = filename[:-4]
        processed.append(pid)
    return processed


def get_classes_dict(path_to_original):
    """
    Get the list of classes for the espresso task
    """
    path = path_to_original / "classes.txt"
    f = open(str(path), "r")
    class_dict = {}
    for line in f.readlines():
        line = line.strip()
        div = line.split(",")
        if len(div) == 1:
            label = div[0].strip()
            lab = label.split(" - ")
            class_dict[label] = lab[-1]
        else:
            label, c = div
            label = label.strip()
            class_dict[label] = c.strip()

    return class_dict


def get_clap_times(path_to_original):
    """
    clap times is a dict that maps from PID to clap time in ms
    """
    path = path_to_original / "clap_times.csv"
    f = open(str(path), "r")
    _ = f.readline()
    clap_dict = {}
    for line in f.readlines():
        pid, time = line.strip().split(",")
        clap_dict[pid] = time.strip()
    return clap_dict


def get_participant_labels(df):
    """
    get the labels for the participant_name
    """
    n = len(df) - 1
    times = np.zeros(n)
    # timestamp[0] is always the header
    # timestamp[1] is always the clap timestamp (that's how it was designed in
    # the tool 3..2..1..clap)
    times = (df.iloc[1:]["Timestamp"] - df.iloc[1]
             ["Timestamp"])  # relative from clap
    times = list(times / 2)  # watched video on half speed
    tasks = list(df["Task"][1:])
    return (times, tasks)