import mass_eval


if __name__ == '__main__':

    mass_eval.config.mus_base_path = '/vol/vssp/maruss/data2/MUS2017'
    mass_eval.config.dsd_base_path = '/vol/vssp/datasets/audio/DSD100'

    df = mass_eval.data_management.get_sisec_df()

    sample = mass_eval.sample_stimuli.get_sample(df,
                                                 num_tracks=2,
                                                 num_algos=4,
                                                 metric='SDR',
                                                 target='vocals',
                                                 selection_plot=True)
