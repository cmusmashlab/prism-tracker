import functools
import pathlib
import pickle
from typing import Union

import numpy as np
import numpy.typing as npt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

from ..config import datadrive


@functools.lru_cache(maxsize=None)
def load_pickle(pickle_path: Union[str, pathlib.Path]):
    with open(pickle_path, 'rb') as pickle_fp:
        return pickle.load(pickle_fp)


def train_classifier(X: npt.ArrayLike, y: npt.ArrayLike, num_classes: int, model_hash: str = None):
    # add dummy data for classes not appeared
    for class_id in range(num_classes):
        if class_id not in y:
            X = np.vstack((X, np.zeros((1, X.shape[1]))))
            y = y + [class_id]

    model_cache_dir = datadrive / 'model_caches'
    if model_cache_dir.exists() and model_hash is not None:
        model_cache_path = model_cache_dir / f'{model_hash}.pkl'
        if model_cache_path.exists():  # use cached models
            return load_pickle(model_cache_path)

    clf = RandomForestClassifier()
    clf.fit(X, y)

    if model_cache_dir.exists() and model_hash is not None:
        with open(model_cache_path, 'wb') as model_fp:
            pickle.dump(clf, model_fp)

    return clf


def obtain_confusion_probabilities(clf, X: npt.ArrayLike, y: npt.ArrayLike, num_classes: int = None):
    labels = None if num_classes is None else range(num_classes)
    cm = confusion_matrix(y, clf.predict(X), labels=labels).astype(np.float64)
    cm /= cm.sum(axis=1, keepdims=True)
    return cm
