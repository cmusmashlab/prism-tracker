import pickle as pkl

from prism_tracker import config
from prism_tracker.preprocessing.annotation import (load_annotations_dict,
                                                    load_clap_times,
                                                    load_classes_dict,
                                                    load_processed)
from prism_tracker.preprocessing.audio import preprocess_audio
from prism_tracker.preprocessing.feature_extraction import (
    build_motion_only_model, build_audio_only_model, create_feature_pkl)
from prism_tracker.preprocessing.motion import preprocess_motion

root_path = config.datadrive / 'tasks' / 'latte_making'
path_to_original = root_path / 'original'
path_to_preprocessed = root_path / 'preprocessed'
path_to_preprocessed.mkdir(exist_ok=True, parents=True)

# load the data
annotations = load_annotations_dict(path_to_original)
classes_dict = load_classes_dict(path_to_original)
clap_dict = load_clap_times(path_to_original)

# check if we've already processed these participants -> returns a list of
# participants that are done
done = load_processed(path_to_preprocessed)
done = [p for p in done if 'kiyosu' not in p]
# done = []
print('done file: ', done)

processed = []
raw_audio_dir = path_to_original / 'audio' / 'raw'

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

    preprocess_audio(participant_name, path_to_original, clap_dict)
    preprocess_motion(participant_name, path_to_original, clap_dict)
    processed.append(participant_name)

print('newly preprocessed: ', processed)
audio_model = build_audio_only_model()
imu_model = build_motion_only_model()

for pid in processed:
    try:
        dataset = create_feature_pkl(
            pid,
            annotations,
            path_to_original,
            classes_dict,
            audio_model,
            imu_model)
        with open(path_to_preprocessed / f'{pid}.pkl', 'wb') as f:
            pkl.dump(dataset, f)
    except BaseException as e:
        print(f'Error in creating feature for {pid}: ', e)
