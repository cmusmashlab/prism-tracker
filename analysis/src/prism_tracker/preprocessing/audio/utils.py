import librosa
import soundfile

from .. import params
from .vggish_input import wavfile_to_examples

def get_audio_examples(audio_file_path):
    """create examples from wavfile.
    """
    leh = 10
    ueh = params.SAMPLE_RATE // 2
    return wavfile_to_examples(audio_file_path, lower_edge_hertz=leh, upper_edge_hertz=ueh)


def preprocess_audio(participant_name, path_to_original, clap_dict):
    """
    Resample the audio to 16kHz and save
    """
    chunk_name = f'{participant_name}.wav'

    path_to_whole = path_to_original / 'audio' / 'WholeFiles' / f'{chunk_name}'
    path_to_save = path_to_whole.parent.parent / "Processed"
    path_to_save.mkdir(exist_ok=True, parents=True)

    # load with librosa in order to downsample to params.SAMPLE_RATE (=16000 by default)
    fdata, _ = librosa.load(path_to_whole, sr=params.SAMPLE_RATE)

    # use the clap dict to find the clap index
    # clap dict is in ms, so first /1000 to convert to secs
    # then x16000 to get the sample id
    clap_index = int(float(clap_dict[participant_name]) * params.SAMPLE_RATE/ 1000)

    # now clip the data that is before the clap
    final_data = fdata[clap_index:]

    # times, tasks = get_distributions(data[participant_name])
    soundfile.write(str(path_to_save / chunk_name),
                    final_data, samplerate=params.SAMPLE_RATE)
