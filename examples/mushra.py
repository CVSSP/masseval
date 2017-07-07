if __name__ == '__main__':

    import mass_eval
    import pandas as pd
    import numpy as np

    mass_eval.config.mus_base_path = '~/data/MUS2017'
    mass_eval.config.dsd_base_path = '~/data/DSD100'
    mass_eval.config.mushra_config_file = './mushra.yaml'

    df = mass_eval.data.get_sisec_df()

    exclude_tracks = []
    mix_sample = pd.DataFrame()
    for metric in ['SDR', 'SAR', 'SIR']:

        sample = mass_eval.data.get_sample(
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

    mass_eval.mushra.mushra_mixture_from_track_sample(mix_sample,
                                                      '.',
                                                      target_loudness=-26,
                                                      mixing_levels=[0, 6, 12])
