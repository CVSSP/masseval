import pkg_resources

dsd_yaml = pkg_resources.resource_filename('mass_eval',
                                           'data/DSD100.yaml')

mus_csv = pkg_resources.resource_filename('mass_eval',
                                          'data/sisec_mus_2017_full.csv')

mushra_yaml = pkg_resources.resource_filename('mass_eval',
                                              'data/mushra.yaml')

# User configurable:
mus_base_path = None
dsd_base_path = None
fs = 44100
audio_encoding = 'float32'
mushra_config_file = mushra_yaml
