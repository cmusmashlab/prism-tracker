import pickle as pkl

import numpy as np
import pandas as pd
from tensorflow.keras.models import Model, load_model

from .. import config
from . import params
from .annotation import get_participant_labels
from .audio import get_audio_examples
from .motion import get_motion_examples



def build_sound_only_model():
    path_to_model = config.datadrive / 'pretrained_models/sound_model.h5'
    ubicoustics_model = load_model(path_to_model)
    fc2_op = ubicoustics_model.get_layer('fc2').output
    final_model = Model(
        inputs=ubicoustics_model.inputs,
        outputs=fc2_op,
        name='somohar_sound_model')
    return final_model


def build_motion_only_model():
    path_to_model = config.datadrive / 'pretrained_models/motion_model.h5'
    motion_model = load_model(path_to_model)
    dense2_op = motion_model.get_layer('dense_2').output
    final_model = Model(
        inputs=motion_model.inputs,
        outputs=dense2_op,
        name='somohar_motion_model')
    return final_model


def get_normalization_params():
    path_to_params = config.datadrive / 'pretrained_models/motion_norm_params.pkl'
    with open(path_to_params, 'rb') as f:
        norm_params = pkl.load(f)

    return norm_params


def get_label(t, times, tasks, class_dict):
    if t < times[0] or t > times[-1]:
        return 'Other'
    for i, time in enumerate(times):
        if t < time:
            label = class_dict[tasks[i - 1].strip()]
            return label


def normalize_motion(motion, norm_params):
    pseudo_max = norm_params['max']
    pseudo_min = norm_params['min']
    mean = norm_params['mean']
    std = norm_params['std']

    motion_normalized = 1 + (motion - pseudo_max) * 2 / (pseudo_max - pseudo_min)
    motion_normalized = (motion_normalized - mean) / std
    return motion_normalized


def create_feature_pkl(pid, annotations, path_to_original,
                       class_dict, sound_model, motion_model):
    # load annotations
    # times is a list of timestamps in ms
    # tasks is a list of corresponding task labels
    times, tasks = get_participant_labels(annotations[pid])

    # load data
    print(f"\n----{pid}----")
    audio_file_path = path_to_original / "audio/Processed" / f'{pid}.wav'
    motion_file_path = path_to_original / "motion/Processed" / f'{pid}.txt'

    motion_df = pd.read_csv(motion_file_path, delim_whitespace=True, header=0)
    motion = motion_df.to_numpy()[:, 1:]

    norm_params = get_normalization_params()
    motion_normalized = normalize_motion(motion, norm_params)

    # generate examples
    imu_examples = get_motion_examples(motion_normalized)
    audio_examples = get_audio_examples(audio_file_path)

    # align motion and audio
    windowed_data_audio = []
    windowed_data_imu = []
    labels = []
    relative_times = []

    # loop through all the audio examples and
    for i in range(audio_examples.shape[0]):
        end_audio_sec = params.EXAMPLE_WINDOW_SECONDS + params.EXAMPLE_HOP_SECONDS * i
        imu_sample_num = 50 * end_audio_sec
        imu_example_index = int(
            (imu_sample_num -
             params.WINDOW_LENGTH_IMU) /
            params.HOP_LENGTH_IMU)

        # (100, 9)
        if imu_example_index >= imu_examples.shape[0]:
            print(
                f'out of bounds {imu_example_index=} {imu_examples.shape[0]=} {i=} {audio_examples.shape[0]=}')
            break
        imu = imu_examples[imu_example_index, :, :]

        # get the timestamp from the motion data
        last_frame_index_motion_example = int(
            imu_example_index *
            params.HOP_LENGTH_IMU +
            params.WINDOW_LENGTH_IMU)
        ms = motion_df["timestamp"][last_frame_index_motion_example]
        try:
            label = get_label(ms, times, tasks, class_dict)
            labels.append(label)
            relative_times.append(end_audio_sec * 1000)
            windowed_data_imu.append(imu)
            windowed_data_audio.append(audio_examples[i])
        except BaseException:
            continue  # remove REMOVE class label

    windowed_arr_audio = np.array(windowed_data_audio)
    windowed_arr_imu = np.array(windowed_data_imu)

    # remove other from the beginning and the end
    audio, imu, strip_labels, new_times = clean_tasks(
        windowed_arr_audio, windowed_arr_imu, labels, relative_times)

    audio_feat = np.array(sound_model([audio]))
    imu_feat = np.array(motion_model([imu]))

    dataset = {
        "IMU": imu_feat,
        "audio": audio_feat,
        "labels": strip_labels,
        "timestamp": new_times
    }

    # print(f'{imu_feat.shape=}, {audio_feat.shape=}, {len(strip_labels)=}, {len(new_times)=}')
    return dataset

def clean_tasks(windowed_arr_audio, windowed_arr_imu, labels, times):
    """delete beginning and end examples classified as "Other"
    """
    print("windowed audio", windowed_arr_audio.shape)
    print("windowed imu", windowed_arr_imu.shape)
    print("labels and times length", len(labels), len(times))
    other_categories = ["Other", "clap", "14"]

    assert windowed_arr_imu.shape[0] == windowed_arr_audio.shape[0]
    assert windowed_arr_imu.shape[0] == len(labels)
    assert windowed_arr_imu.shape[0] == len(times)

    # remove Other from start and end
    i = 0
    j = len(labels) - 1
    while (i < len(labels)):
        if str(labels[i]) in other_categories:
            i += 1
        else:
            break
    while (j >= 0):
        if str(labels[j]) in other_categories:
            j -= 1
        else:
            break

    audio = windowed_arr_audio[i:j + 1,]
    imu = windowed_arr_imu[i:j + 1,]
    # if (i-1 >= 0 and j+1 < len(labels)):
    #     print("other cutoffs: ", i, j, len(labels))
    #     print(f'{labels[i-1]=}, {labels[i]=}, {labels[j]=}, {labels[j+1]=}')
    labels = labels[i:j + 1]
    times = times[i:j + 1]
    print(" removed other at the beginning and ending.",
          audio.shape, imu.shape, len(labels), len(times))
    assert (len(labels) == audio.shape[0] == imu.shape[0] == len(times))

    return audio, imu, labels, times
