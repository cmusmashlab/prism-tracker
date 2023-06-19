import pickle as pkl

from prism_tracker import config
from prism_tracker.preprocessing.annotation import (
    load_annotations_dict, load_clap_times, load_classes_dict, load_processed,
)
from prism_tracker.preprocessing.audio import preprocess_audio
from prism_tracker.preprocessing.feature_extraction import (
    build_audio_only_model, build_motion_only_model, create_feature_pkl,
)
from prism_tracker.preprocessing.motion import preprocess_motion

root_path = config.datadrive / 'tasks' / 'latte_making'
dataset_dir = root_path / 'dataset'
preprocessed_dir = root_path / 'preprocessed'
preprocessed_dir.mkdir(exist_ok=True, parents=True)

# load the data
annotations = load_annotations_dict(dataset_dir)
classes_dict = load_classes_dict(dataset_dir)
clap_dict = load_clap_times(dataset_dir)

# check if we've already processed these participants -> returns a list of
# participants that are done
done = load_processed(preprocessed_dir)
print('done file: ', done)

processed = []
raw_audio_dir = dataset_dir / 'audio' / 'raw'

for fpath in raw_audio_dir.iterdir():

    if not fpath.is_file():
        continue
    print(f'\n-----preprocess {fpath.name}-----')
    participant_name = fpath.stem
    if (participant_name not in annotations):
        print(f'{participant_name} not in csv file')
        continue
    if (participant_name in done):
        print(f'{participant_name} already done')
        continue
    if (participant_name not in clap_dict):
        print(f'Skipping {participant_name}, cannot find clap time')
        continue

    preprocess_audio(participant_name, dataset_dir, clap_dict)
    preprocess_motion(participant_name, dataset_dir, clap_dict)
    processed.append(participant_name)

print('newly preprocessed: ', processed)
audio_model = build_audio_only_model()
imu_model = build_motion_only_model()

for pid in processed:
    try:
        dataset = create_feature_pkl(
            pid,
            annotations,
            dataset_dir,
            classes_dict,
            audio_model,
            imu_model)
        with open(preprocessed_dir / f'{pid}.pkl', 'wb') as f:
            pkl.dump(dataset, f)
    except BaseException as e:
        print(f'Error in creating feature for {pid}: ', e)
