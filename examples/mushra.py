if __name__ == '__main__':

    import masseval
    import pandas as pd
    import numpy as np

    masseval.config.mus_base_path = '/vol/vssp/maruss/data2/MUS2017'
    masseval.config.dsd_base_path = '/vol/vssp/datasets/audio/DSD100'
    masseval.config.mushra_config_file = './mushra.yaml'

    df = masseval.data.get_sisec_df()

    exclude_tracks = []
    mix_sample = pd.DataFrame()
    for metric in ['SDR', 'SAR', 'SIR']:

        sample = masseval.data.get_sample(
                df,
                num_tracks=2,
                num_algos=4,
                metric=metric,
                target='vocals',
                only_these_algos=None,
                exclude_tracks=exclude_tracks,
                selection_plot=False)

        tracks = sample['track_id'].values
        exclude_tracks = np.append(exclude_tracks, np.unique(tracks))
        mix_sample = pd.concat([mix_sample, sample])

    masseval.mushra.mixture_from_track_sample(mix_sample,
                                              '.',
                                              target_loudness=-26,
                                              mixing_levels=[0, 6, 12])
