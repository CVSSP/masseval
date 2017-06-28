import numpy as np


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


def count_outliers(df):
    return np.sum(find_outliers)
