import functools
import hashlib
import itertools
import multiprocessing
import os
import pathlib
import pickle
import warnings
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
from sklearn.model_selection import LeaveOneOut, train_test_split

from ..tracker.collections import Graph
from ..tracker.viterbi import ViterbiTracker
from .classifier import obtain_confusion_probabilities, train_classifier


def load_imu_and_audio_data(pickle_files: List[Union[str, pathlib.Path]],
                            steps: List[str]) -> Tuple[npt.NDArray, List[int]]:
    """
    This function loads IMU and audio data from a set of pickle files and converts the labels into numerical values based on their index in a list of steps.

    Args:
    * pickle_files (List[Union[str, pathlib.Path]]): a list of paths to the pickle files containing IMU and audio data.
    * steps (List[str]): a list of strings representing the different steps in the procedure.

    Returns:
    * X (npt.NDArray): a 2D numpy array containing the frame-based time-series IMU and audio data.
    * y (List[int]): a list of integers representing the index of the step for each time frame.
    """
    X, y = None, []

    for pickle_file in pickle_files:
        with open(pickle_file, 'rb') as fp:
            data = pickle.load(fp)

        imu_data, audio_data, labels = [], [], []
        for i, label in enumerate(data['labels']):
            if label != 'Other':
                imu_data.append(data['IMU'][i])
                audio_data.append(data['audio'][i])
                labels.append(label)

        x = np.hstack((np.array(imu_data), np.array(audio_data)))
        if X is None:
            X = x
        else:
            X = np.vstack((X, x))

        labels = list(map(lambda l: steps.index(l), labels))
        y += labels

    return X, y


def obtain_predictions(train_files: List[Union[str, pathlib.Path]], val_files: List[Union[str, pathlib.Path]],
                       test_files: List[Union[str, pathlib.Path]], graph: Graph, steps: List[str],
                       start_step_indices: Optional[List[int]] = None, oracle_step_indices: Optional[List[int]] = None
                       ) -> Tuple[List[List[List[int]]], List[List[List[int]]], List[List[List[int]]]]:
    """
    This function obtains predictions for a set of test files given a set of training files and validation files, using the Viterbi algorithm to track predicted steps.

    Args:
    * train_files (List[Union[str, pathlib.Path]]): a list of the paths to the training files containing the input data.
    * val_files (List[Union[str, pathlib.Path]]): a list of the paths to the validation files containing the input data.
    * test_files (List[Union[str, pathlib.Path]]): a list of the paths to the test files containing the input data.
    * graph (Graph): a graph object built using build_graph(), which represents transitions between the different steps in a procedure.
    * steps (List[str]): a list of strings representing the steps in the process.
    * start_step_indices (Optional[List[int]]): a list of integers representing the indices of the starting step.
    * oracle_step_indices (Optional[List[int]]): a list of integers representing the indices of the steps we can provide oracle information.

    Returns:
    * y_true_all (List[List[List[int]]]): a list of true labels, calculated for all of the past frames at each time frame of each test file.
    * y_pred_raw_all (List[List[List[int]]]): a list of predicted labels (without Viterbi correction) labels, calculated for all of the past frames at each time frame of each test file.
    * y_pred_viterbi_all (List[List[List[int]]]): a list of predicted labels (with Viterbi correction labels, calculated for all of the past frames at each time frame of each test file.
    """
    warnings.filterwarnings('ignore')

    X_train, y_train = load_imu_and_audio_data(train_files, steps)
    train_hash = hashlib.md5(','.join(sorted(map(str, train_files))).encode('utf-8')).hexdigest()
    clf = train_classifier(X_train, y_train, num_classes=len(steps), model_hash=train_hash)

    X_val, y_val = load_imu_and_audio_data(val_files, steps)
    cm_val = obtain_confusion_probabilities(clf, X_val, y_val, num_classes=len(steps))

    viterbi = ViterbiTracker(graph, start_step_indices=start_step_indices)
    y_true_all, y_pred_raw_all, y_pred_viterbi_all = [], [], []

    for test_file in test_files:  # predict per data
        X, y = load_imu_and_audio_data([test_file], steps)

        inputs = clf.predict_proba(X)  # times x labels
        pred_raw = inputs.argmax(axis=1)

        oracle: Dict[int, List[int]] = {}  # {step_index: [transition_time, ...]}
        if oracle_step_indices is not None:
            for index in oracle_step_indices:
                acc_time = 0
                for key, group in itertools.groupby(y):
                    if key == index:
                        oracle[index] = oracle.get(index, []) + [acc_time]
                    acc_time += len(list(group))

        y_true, y_pred_raw, y_pred_viterbi = [], [], []
        for pred_prob, pred_steps in viterbi.predict(inputs.T, cm_val, oracle=oracle):
            pred_steps_with_others = pred_steps

            y_true.append(y[:len(pred_steps_with_others)])
            y_pred_raw.append(list(pred_raw[:len(pred_steps_with_others)]))
            y_pred_viterbi.append(list(pred_steps_with_others))

        y_true_all.append(y_true)
        y_pred_raw_all.append(y_pred_raw)
        y_pred_viterbi_all.append(y_pred_viterbi)

    return y_true_all, y_pred_raw_all, y_pred_viterbi_all


def perform_loo(graph: Graph, pickle_files: List[Union[str, pathlib.Path]], steps: List[str],
                start_step_indices: Optional[List[int]] = None, oracle_step_indices: Optional[List[int]] = None,
                num_processes: int = 12) -> Tuple[List[List[List[int]]], List[List[List[int]]], List[List[List[int]]]]:
    """
    This function performs a leave-one-out evaluation of with a provided set of input data.

    Args:
    * graph (Graph): A graph object with a list of step objects and a dictionary containing transition probabilities.
    * pickle_files (List[Union[str, pathlib.Path]]): a list of the paths to the pickle files containing the input data.
    * steps (List[str]): a list of strings representing the steps in the process.
    * start_step_indices (Optional[List[int]]): a list of integers representing the indices of the starting step.
    * oracle_step_indices (Optional[List[int]]): a list of integers representing the indices of the steps we can provide oracle information.
    * num_processes (int): the number of processes to use for multiprocessing.

    Returns:
    * y_true_all (List[List[List[int]]]): a list of true labels, calculated for all of the past frames at each time frame of each test file.
    * y_pred_raw_all (List[List[List[int]]]): a list of predicted labels (without Viterbi correction) labels, calculated for all of the past frames at each time frame of each test file.
    * y_pred_viterbi_all (List[List[List[int]]]): a list of predicted labels (with Viterbi correction labels, calculated for all of the past frames at each time frame of each test file.
    """
    y_true_all, y_pred_raw_all, y_pred_viterbi_all = [], [], []

    prediction_func = functools.partial(obtain_predictions, graph=graph, steps=steps,
                                        start_step_indices=start_step_indices, oracle_step_indices=oracle_step_indices)
    args = []

    shuffler = np.random.RandomState(0)
    for train_indices, test_indices in LeaveOneOut().split(pickle_files):
        # train:val:test = 8:2
        train_indices, val_indices = train_test_split(train_indices, test_size=0.2, random_state=shuffler)

        train_files = [pickle_files[index] for index in train_indices]
        val_files = [pickle_files[index] for index in val_indices]
        test_files = [pickle_files[index] for index in test_indices]

        # use the data from authors only for training, not to include into the evaluation
        test_files = list(filter(lambda x: not os.path.basename(x).endswith('-authors.pkl'), test_files))
        if len(test_files) > 0:
            args.append((train_files, val_files, test_files))

    pool = multiprocessing.Pool(num_processes)
    for y_true, y_pred_raw, y_pred_viterbi in pool.starmap(prediction_func, args):
        y_true_all += y_true
        y_pred_raw_all += y_pred_raw
        y_pred_viterbi_all += y_pred_viterbi

    return y_true_all, y_pred_raw_all, y_pred_viterbi_all
