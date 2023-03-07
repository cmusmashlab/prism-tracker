import numpy as np
import pandas as pd

from .. import params


def get_motion_examples(motion_data):
    """
    Get motion data by windows.
    """
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
    return np.lib.stride_tricks.as_strided(
        motion_data, shape=shape, strides=strides)


def reset_times_relative_to_clap(df, clap_ms):
    """
    Reset the timestamps based on the clap_dict.
    """
    df['timestamp'] *= 1000  # convert to ms (from secs)
    df['timestamp'] -= df['timestamp'][0]  # start sensor time at zero
    df['timestamp'] -= float(clap_ms)  # zero to clap

    # now only keep timestamps that are >= 0
    df = df[df['timestamp'] >= 0]
    return df


def preprocess_motion(participant_name, original_dir, clap_dict):
    """
    Set the proper timestamps and remove data before clap.
    """

    raw_fp = original_dir / 'motion' / 'raw' / \
        f'{participant_name}-realtime.txt'

    sensor_columns = ['unix_time', 'data.userAcceleration.x', 'data.userAcceleration.y', 'data.userAcceleration.z',
                      'data.gravity.x', 'data.gravity.y', 'data.gravity.z',
                      'data.rotationRate.x', 'data.rotationRate.y', 'data.rotationRate.z',
                      'data.magneticField.field.x', 'data.magneticField.field.y', 'data.magneticField.field.z',
                      'data.attitude.roll', 'data.attitude.pitch', 'data.attitude.yaw',
                      'data.attitude.quaternion.x', 'data.attitude.quaternion.y', 'data.attitude.quaternion.z',
                      'data.attitude.quaternion.w', 'data.time']

    df = pd.read_csv(
        raw_fp,
        delim_whitespace=True,
        header=None,
        names=sensor_columns)

    save_df = pd.DataFrame()
    save_df['timestamp'] = df['data.time']  # use the sensor timestamp
    save_df['acc.x'] = - (df['data.userAcceleration.x'] + df['data.gravity.x']) * 9.81
    save_df['acc.y'] = - (df['data.userAcceleration.y'] + df['data.gravity.y']) * 9.81
    save_df['acc.z'] = - (df['data.userAcceleration.z'] + df['data.gravity.z']) * 9.81

    save_df = reset_times_relative_to_clap(
        save_df, clap_dict[participant_name])

    save_fp = original_dir / 'motion' / \
        'preprocessed' / f'{participant_name}.txt'
    save_fp.parent.mkdir(exist_ok=True, parents=True)
    save_df.to_csv(save_fp, index=None, sep=' ', mode='w')
