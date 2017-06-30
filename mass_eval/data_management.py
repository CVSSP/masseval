import pandas as pd
import mass_datasets
from . import config


def get_sisec_df():

    '''
    Returns the SiSEC17 data as a pandas DataFrame, excluding the test set and
    ideal binary mask.
    Note tracks, 36, 37 and 43 are not included in the results file nor are
    they available to listen to online. This is because the original DSD100
    files were currupt, and thus have been excluded from the submissions.
    '''

    df = pd.read_csv(config.mus_csv)

    # test set only, no IBM
    df = df[(df.is_dev == 0) &
            (df.method != 'IBM') &
            (df.target.isin(['bass',
                             'drums',
                             'other',
                             'accompaniment',
                             'vocals']))
            ]

    # Ensure we have all four stems per song
    df = df.groupby(['title', 'method']).filter(
        lambda g: set(g.target) == set(['bass', 'drums', 'other',
                                        'accompaniment', 'vocals'])
    )

    filepaths = get_audio_filepaths(df)
    df['filepath'] = filepaths

    return df


def get_dsd100_df(base_path=config.dsd_base_path):

    ds = mass_datasets.Dataset.read(config.dsd_yaml)

    ds.base_path = base_path
    frame = ds.to_pandas_df()

    return frame


def get_audio_filepaths(df):
    '''
    Given a DataFrame derived from SiSEC2017 csv,
    returns a Series of filepaths to the wav files in MUS2017.
    Indices correspond to those in the given DataFrame.
    '''

    frame = get_dsd100_df(config.mus_base_path)

    files_to_get = []
    for idx, row in df.iterrows():

        title = row['title'].split('- ')[1]

        # Fix for accompaniment as it is not included in DSD data base
        is_accompaniment = False
        if row['target'] == 'accompaniment':
            is_accompaniment = True
            row['target'] = 'vocals'

        sub = frame[(frame['title'].str.contains(title)) &
                    (frame['audio'] == row['target'])].copy()

        if is_accompaniment:
            sub['audio_filepath'].replace(
                r'vocals', 'accompaniment', regex=True, inplace=True)
            sub['audio'] = 'accompaniment'

        fn = sub['audio_filepath'].replace(
            r'Sources', row['method'], regex=True).values[0]

        files_to_get.append(fn)

    return pd.Series(files_to_get, index=df.index)


def append_dsd100_filepaths(sample):
    '''
    Accompaniment will be dropped if included (as not part of DSD100).
    '''

    df = get_dsd100_df(config.dsd_base_path)

    sample = sample.copy()

    sample['ref_filepath'] = None

    for idx, g in sample.iterrows():

        if g['target'] != 'accompaniment':

            title = g['title'].split('- ')[1]

            temp = df[(df['title'].str.contains(title)) &
                      (df['audio'] == g['target'])]

            sample.loc[idx, 'ref_filepath'] = temp['audio_filepath'].values[0]

    return sample


def get_reference_filepath(df):
    '''
    Given a DataFrame with the sisec17 data, returns the filepaths of the
    corresponding reference stimuli from DSD100.
    '''

    frame = get_dsd100_df(config.dsd_base_path)

    group = df.groupby('track_id')

    out = pd.DataFrame()
    for idx, g in group:

        row = g.iloc[0]

        title = row['title'].split('- ')[1]

        temp = frame[(frame['title'].str.contains(title)) &
                     (frame['audio'] == row['target'])].copy()

        temp['track_id'] = row['track_id']
        temp.rename(columns={'audio_filepath': 'filepath'}, inplace=True)

        out = out.append(temp)

    return out


def get_others_filepaths(df):
    '''
    Given a DataFrame with the sisec17 data, returns the filepaths of the
    corresponding reference stimuli from DSD100.
    '''

    frame = get_dsd100_df(config.dsd_base_path)

    group = df.groupby('track_id')

    out = pd.DataFrame()
    for idx, g in group:

        row = g.iloc[0]

        title = row['title'].split('- ')[1]

        temp = frame[(frame['title'].str.contains(title)) &
                     (frame['audio'] != row['target']) &
                     (frame['audio'] != 'mixture')].copy()

        temp['track_id'] = row['track_id']
        temp.rename(columns={'audio_filepath': 'filepath'}, inplace=True)

        out = out.append(temp)

    return out
