import mass_eval


if __name__ == '__main__':

    mass_eval.config.mus_base_path = '/vol/vssp/maruss/data2/MUS2017'
    mass_eval.config.dsd_base_path = '/vol/vssp/datasets/audio/DSD100'

    # Load the SISEC dataframe
    df = mass_eval.dataframes.get_sisec_df()

    # Take a sample
    sample = mass_eval.sample.get_sample(df,
                                         num_tracks=2,
                                         num_algos=2,
                                         metric='SDR',
                                         target='vocals',
                                         selection_plot=False)

    # Write mixtures
    mass_eval.audio.write_mixtures_from_sample(sample,
                                               'vocals',
                                               '/scratch',
                                               force_mono=True,
                                               target_loudness=-26,
                                               mixing_levels=[0])

    # Write target only
    mass_eval.audio.write_target_from_sample(sample,
                                             'vocals',
                                             '/scratch',
                                             force_mono=True,
                                             target_loudness=-26)
