import numpy as np
import pandas as pd

from .. import params

def get_motion_examples(motion_data):
    window_length = params.WINDOW_LENGTH_IMU
    hop_length = params.HOP_LENGTH_IMU

    if motion_data.shape[0] < window_length:
        # pad zeros
        len_pad = int(np.ceil(window_length)) - motion_data.shape[0]
        to_pad = np.zeros((len_pad, ) + motion_data.shape[1:])
        motion_data = np.concatenate([motion_data, to_pad], axis=0)
    num_samples = motion_data.shape[0]
    num_frames = 1 + int(np.floor((num_samples - window_length) / hop_length))
    shape = (num_frames, int(window_length)) + motion_data.shape[1:]
    strides = (motion_data.strides[0] * int(hop_length),) + motion_data.strides
    return np.lib.stride_tricks.as_strided(motion_data, shape=shape, strides=strides)


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


def reset_times_relative_to_clap(df, clap_ms):
    """
    reset the timestamps based on the clap_dict
    """
    df["timestamp"] *= 1000  # convert to ms (from secs)
    df["timestamp"] -= df["timestamp"][0]  # start sensor time at zero
    df["timestamp"] -= float(clap_ms)  # zero to clap

    # now only keep timestamps that are >= 0
    df = df[df["timestamp"] >= 0]
    return df


def preprocess_motion(participant_name, path_to_original, clap_dict):
    """
    set's the proper timestamps and removes remove data before timestamps
    """
    path_to_whole = path_to_original / "motion/WholeFiles"
    path_to_save = path_to_whole.parent / "Processed"

    file_path = path_to_whole / f"{participant_name}-realtime.txt"

    apple_watch_columns = ["unix_time", "data.userAcceleration.x", "data.userAcceleration.y", "data.userAcceleration.z",
                           "data.gravity.x", "data.gravity.y", "data.gravity.z",
                           "data.rotationRate.x", "data.rotationRate.y", "data.rotationRate.z",
                           "data.magneticField.field.x", "data.magneticField.field.y", "data.magneticField.field.z",
                           "data.attitude.roll", "data.attitude.pitch", "data.attitude.yaw",
                           "data.attitude.quaternion.x", "data.attitude.quaternion.y", "data.attitude.quaternion.z",
                           "data.attitude.quaternion.w", "data.time"]

    df = pd.read_csv(
        file_path,
        delim_whitespace=True,
        header=None,
        names=apple_watch_columns)

    save = pd.DataFrame()
    save["timestamp"] = df["data.time"]  # use the sensor timestamp

    # convert the apple watch data to the same frame of reference as the j
    save["acc.x"] = - (df["data.userAcceleration.x"] +
                       df["data.gravity.x"]) * 9.81
    save["acc.y"] = - (df["data.userAcceleration.y"] +
                       df["data.gravity.y"]) * 9.81
    save["acc.z"] = - (df["data.userAcceleration.z"] +
                       df["data.gravity.z"]) * 9.81

    save = reset_times_relative_to_clap(save, clap_dict[participant_name])

    save_path = path_to_save / f"{participant_name}.txt"
    save_path.parent.mkdir(exist_ok=True, parents=True)
    save.to_csv(save_path, index=None, sep=' ', mode="w")
