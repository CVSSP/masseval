from . import dataframes
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb


def interquartile_range(df):
    return df.quantile(0.75) - df.quantile(0.25)


def find_outliers(df):
    q1, q3 = df.quantile(0.25), df.quantile(0.75)
    iqr = q3 - q1
    return (df < q1 - iqr * 1.5) | (df > q3 + iqr * 1.5)


def diff_sampler(df, size):

    df = df.sort_values()

    step = (np.max(df) - np.min(df)) / (size - 1)
    alpha = 0.01

    idx = []
    while True:

        idx = [0]
        val_prev = df.iloc[0]

        for i, val in enumerate(df[1:]):
            if (val - val_prev) >= step:
                idx.append(i + 1)
                val_prev = val

        if len(idx) > size:
            step *= 1 + alpha
        elif len(idx) < size:
            step *= alpha
        else:
            break

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
        sub_df = sub_df[sub_df.method.isin(only_these_algos)]

    if exclude_tracks is not None:
        sub_df = sub_df[~sub_df.track_id.isin(exclude_tracks)]

    sample = sample_stimuli_algos(sub_df,
                                  num_tracks=num_tracks,
                                  num_algos=num_algos,
                                  remove_outliers=True)

    if selection_plot:
        plt.figure(1)
        sb.boxplot(sub_df.score, groupby=sub_df.track_id)
        sb.swarmplot(sub_df.track_id, sub_df.score, color=".25")
        plt.show()

        plt.figure(2)
        sb.boxplot(sample.score, groupby=sample.track_id)
        sb.swarmplot(sample.track_id, sample.score, color=".25")
        plt.show()

    # Add all other sources back in
    sample = df[(df.metric == metric) &
                df.track_id.isin(sample.track_id) &
                df.method.isin(sample.method)]

    sample = dataframes.add_reference_to_sample(sample)

    return sample
