import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb
import os
import massdatasets
from . import config


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


def get_sisec_df(must_have_all_sources=True):

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

    if must_have_all_sources:
        df = df.groupby(['title', 'method']).filter(
            lambda g: set(g.target) == set(['bass', 'drums', 'other',
                                            'accompaniment', 'vocals'])
        )

    filepaths = get_audio_filepaths(df)
    df['filepath'] = filepaths

    return df


def get_dsd100_df(base_path=None):

    if not base_path:
        base_path = config.dsd_base_path

    ds = massdatasets.Dataset.read(config.dsd_yaml)

    ds.base_path = base_path
    frame = ds.to_pandas_df()

    return frame


def add_reference_to_sample(sample):

    df = get_dsd100_df(config.dsd_base_path)

    out = pd.DataFrame(columns=sample.columns)
    for idx, group in sample.groupby('track_id'):
        ref = group.iloc[0].copy()
        for stem in ['vocals', 'drums', 'bass', 'other']:
            ref['method'] = 'ref'
            ref['score'] = np.nan
            ref['filename'] = ''
            ref['target'] = stem
            out = out.append(ref)
    out = out.reset_index(drop=True)

    for idx, g in out.iterrows():

        title = g['title'].split('- ')[1]

        temp = df[(df['title'].str.contains(title)) &
                  (df['audio'] == g['target'])]

        out.loc[idx, 'filepath'] = temp['audio_filepath'].values[0]

    out = sample.append(out).reset_index(drop=True)

    return out.sort_values(by=['track_id', 'method', 'target'])


def interquartile_range(df):
    return df.quantile(0.75) - df.quantile(0.25)


def find_outliers(df):
    q1, q3 = df.quantile(0.25), df.quantile(0.75)
    iqr = q3 - q1
    return (df < q1 - iqr * 1.5) | (df > q3 + iqr * 1.5)


def diff_sampler(df, size, num_iters=1000):

    df = df.sort_values()

    if size == 1:
        return df.take([0])

    step = (np.max(df) - np.min(df)) / (size - 1)
    alpha = 0.01

    idx = []
    for i in range(num_iters):

        idx = [0]
        val_prev = df.iloc[0]

        for i, val in enumerate(df[1:]):
            if (val - val_prev) >= step:
                idx.append(i + 1)
                val_prev = val

        if len(idx) > size:
            step *= 1 + alpha
        elif len(idx) < size:
            step *= 1 - alpha
        else:
            return df.take(idx)

    warnings.warn(
        'The returned sample size is {0} but you asked for {1}'.format(
            len(idx), size)
    )

    return df.take(idx)


def sample_stimuli_algos(df,
                         num_tracks=2,
                         num_algos=8,
                         remove_outliers=False):
    '''
    A little hacky:

    Selects num_tracks tracks from the 50 target tracks with num_algos stimuli
    per track.

    Selection is based on looking at the 25 tracks with the widest spread
    and then selecting those which maximise variation in medians.

    num_algos stimuli are then sampled from each of the sorted tracks such that
    variation is maximised.
    '''

    if remove_outliers:
        outliers = df.groupby('track_id')['score'].apply(find_outliers)

        df = df[outliers == False]  # noqa: E712

    # Take IQR for each sample and remove lower 50%
    method_iqr = df.groupby(['track_id']).agg(
        {'score': interquartile_range}).reset_index()

    select = method_iqr[
        method_iqr['score'] > method_iqr['score'].quantile(0.5)]

    df = df[df.track_id.isin(select.track_id)]

    # Now sample to give a spread in medians
    medians = df.groupby(['track_id']).agg(
        {'score': np.median}).reset_index()

    sample = diff_sampler(medians['score'], num_tracks)
    select = medians[medians['score'].isin(sample)]

    df = df[df.track_id.isin(select.track_id)]

    # Now sample algos within each track
    loc = df.groupby('track_id')['score'].apply(
        lambda x: diff_sampler(
            x, num_algos)).reset_index(level=0).index

    df = df.loc[loc]

    return df


def get_sample(df,
               num_tracks=2,
               num_algos=8,
               metric='SDR',
               target='vocals',
               only_these_algos=None,
               exclude_tracks=None,
               exclude_algos_in_tracks=None,
               remove_outliers=False,
               selection_plot=False):
    '''
    filenames are replaced with the actual file location.
    '''

    if isinstance(only_these_algos, str):
        only_these_algos = [only_these_algos]

    sub_df = df[(df.metric == metric) &
                (df.target == target)
                ]

    if only_these_algos is not None:
        if num_algos != len(only_these_algos):
            raise ValueError(('Number of algorithms is {0}, '
                              'but got {1}'.format(num_algos,
                                                   len(only_these_algos))))
        sub_df = sub_df[sub_df.method.isin(only_these_algos)]

    if exclude_tracks is not None:
        sub_df = sub_df[~sub_df.track_id.isin(exclude_tracks)]

    if isinstance(exclude_algos_in_tracks, dict):
        for algo, tracks in exclude_algos_in_tracks.items():
            if not isinstance(tracks, list):
                tracks = list(tracks)

            sub_df = sub_df[~((sub_df.method == algo) &
                              (sub_df.track_id.isin(tracks)))]

    sample = sample_stimuli_algos(sub_df,
                                  num_tracks=num_tracks,
                                  num_algos=num_algos,
                                  remove_outliers=remove_outliers)
    if selection_plot:
        plt.figure(1)
        sb.boxplot(sub_df.score, groupby=sub_df.track_id)
        sb.swarmplot(sub_df.track_id, sub_df.score, color=".25")
        plt.show()

        plt.figure(2)
        sb.boxplot(sample.score, groupby=sample.track_id)
        sb.swarmplot(sample.track_id, sample.score, color=".25")
        plt.show()

    out = pd.DataFrame()
    # Add other sources back in, removing accompaniment if others are present
    for idx, g in sample.groupby(['track_id', 'method']):

        sub = df[(df.metric == metric) &
                 (df.track_id == idx[0]) &
                 (df.method == idx[1])]

        if len(sub.target) == 5:
            sub = sub[sub.target != 'accompaniment']

        out = out.append(sub)

    out = add_reference_to_sample(out)

    return out


def remix_df_from_sample(sample,
                         directory,
                         mixing_levels,
                         target='vocals',
                         ):

    sample = sample.loc[sample.target == target]
    sample_accomp = sample.copy()
    sample_accomp['target'] = 'accomp'
    sample_mixture = sample.copy()
    sample_mixture['target'] = 'mixture'
    sample = pd.concat([sample, sample_accomp, sample_mixture])

    sample.loc[sample.method == 'ref', 'filename'] = ''
    anchor1 = sample[sample.method == 'ref'].copy()
    anchor1['method'] = 'anchor_quality'
    anchor2 = sample[sample.method == 'ref'].copy()
    anchor2['method'] = 'anchor_loudness'
    sample = pd.concat([sample, anchor1, anchor2])

    # Save file paths
    frames = pd.DataFrame()
    for idx, g_sample in sample.groupby('track_id'):

        folder = '{0}-{1}-{2}'.format(
            'mix',
            g_sample.iloc[0]['track_id'],
            g_sample.iloc[0]['metric'])

        full_path = os.path.join(directory, folder)

        for name, method in g_sample.groupby('method'):

            this_method = method.copy()
            for level in mixing_levels:

                this_method['level'] = level
                filename = '{0}/{1}_mix_{2}dB'.format(full_path, name, level)

                this_method.loc[this_method.target == target,
                                'stimulus_path'] = filename + '_target.wav'
                this_method.loc[this_method.target == 'accomp',
                                'stimulus_path'] = filename + '_accomp.wav'
                this_method.loc[this_method.target == 'mixture',
                                'stimulus_path'] = filename + '.wav'

                frames = pd.concat([frames, this_method])

    return frames
