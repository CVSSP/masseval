import masseval


if __name__ == '__main__':

    masseval.config.mus_base_path = '/vol/vssp/maruss/data2/MUS2017'
    masseval.config.dsd_base_path = '/vol/vssp/datasets/audio/DSD100'

    # Load the SISEC dataframe
    df = masseval.dataframes.get_sisec_df()

    # Take a sample
    sample = masseval.sample.get_sample(df,
                                        num_tracks=2,
                                        num_algos=2,
                                        metric='SDR',
                                        target='vocals',
                                        selection_plot=False)

    # Write mixtures
    masseval.audio.write_mixtures_from_sample(sample,
                                              'vocals',
                                              '/scratch',
                                              force_mono=True,
                                              target_loudness=-26,
                                              mixing_levels=[0])

    # Write target only
    masseval.audio.write_target_from_sample(sample,
                                            'vocals',
                                            '/scratch',
                                            force_mono=True,
                                            target_loudness=-26)
