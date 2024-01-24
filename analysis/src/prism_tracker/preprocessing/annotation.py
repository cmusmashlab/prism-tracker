import pandas as pd


def load_annotations_dict(original_dir):
    """
    Load annotations for the task
    """
    df = pd.read_csv(original_dir / 'annotation.csv')

    # fill NaNs with last seen values -> results in the participant id being
    # filled
    df.ffill(inplace=True)

    userdfs = {}
    for user in df['Participant'].unique():
        userdf = df.loc[df['Participant'] == user]
        userdf.reset_index(drop=True)
        userdfs[user] = userdf
    return userdfs


def load_classes_dict(original_dir):
    """
    Load the list of classes for the task.
    """
    path = original_dir / 'classes.txt'
    f = open(str(path), 'r')
    class_dict = {}
    for line in f.readlines():
        line = line.strip()
        div = line.split(',')
        if len(div) == 1:
            label = div[0].strip()
            lab = label.split(' - ')
            class_dict[label] = lab[-1]
        else:
            label, c = div
            label = label.strip()
            class_dict[label] = c.strip()

    return class_dict


def load_clap_times(original_dir):
    """
    Load a dict from csv that maps from PID to clap time in ms.
    """
    path = original_dir / 'clap_times.csv'
    f = open(path, 'r')
    _ = f.readline()
    clap_dict = {}
    for line in f.readlines():
        pid, time = line.strip().split(',')
        clap_dict[pid] = time.strip()
    return clap_dict


def load_processed(processed_dir):
    """
    Load which PIDs are already processed.
    """
    processed = []
    for fp in processed_dir.iterdir():
        pid = fp.stem
        processed.append(pid)
    return processed


def get_times_and_labels(df, half=False):
    """
    Get the times and labels for the given df.
    If annotated by watching a video with 0.5x speed, `half` should be True.
    """
    # timestamp[0] is always the header
    # timestamp[1] is always the clap timestamp (that's how it was designed in
    # the tool 3..2..1..clap)
    times = (df.iloc[1:]['Timestamp'] - df.iloc[1]
             ['Timestamp'])  # relative from clap
    if half:
        times = list(times / 2)  # watched video on half speed
    else:
        times = list(times)
    tasks = list(df['Task'][1:])
    return (times, tasks)


def overwrite_other_labels(labels):
    """
    Overwrite 'Other' labels by their previous label.
    Make sure to remove 'Other' in the beginning and ending before applying this function.
    """
    output = []
    assert labels[0] != 'Other'
    prev = labels[0]
    for label in labels:
        if label != 'Other':
            output.append(label)
            prev = label
        else:
            output.append(prev)
    return output
