import os
import pandas as pd
import yaml


class Dataset(yaml.YAMLObject):
    '''
    Class for creating yaml files for indexing common multitrack audio
    datasets.
    '''

    def __init__(self, base_path):

        self.dataset = self.__class__.__name__
        self.base_path = base_path
        self.songs = []

    @classmethod
    def read(cls, filename=None):
        with open(filename, 'r') as f:
            instance = yaml.load(f)
        return instance

    def write(self, filename=None):
        if filename is None:
            filename = self.dataset
        else:
            filename, ext = os.path.splitext(filename)
        with open(filename + '.yaml', 'w') as f:
            yaml.dump(self, f, default_flow_style=False)

    def dump(self):
        return yaml.dump(self, default_flow_style=False)

    def add_song(self, artist, title, style, audio_filepath, **kwargs):
        self.songs.append(
            {'artist': artist,
             'title': title,
             'style': style,
             'audio_filepath': audio_filepath,
             **kwargs}
        )

    def to_pandas_df(self):
        '''
        Compiles the yaml document to a pandas DataFrame.
        audio_filepath are complete (prefixed by base_path).
        '''

        frame = pd.DataFrame(columns=self.songs[0].keys())

        for song in self.songs:
            sub_frame = pd.DataFrame.from_dict(song)
            sub_frame['audio'] = sub_frame.index
            frame = frame.append(sub_frame, ignore_index=True)

        frame['audio_filepath'] = ['/'.join((self.base_path, _))
                                   for _ in frame['audio_filepath']]
        frame['dataset'] = self.dataset
        return frame


class DSD100(Dataset):

    def __init__(self,
                 base_path='/vol/vssp/datasets/audio/DSD100',
                 xlsx_name='dsd100.xlsx'):
        super(DSD100, self).__init__(base_path)

        base_path = os.path.abspath(base_path)

        excel = pd.read_excel(os.path.join(base_path, xlsx_name), 'Sheet1')

        # Fix typo in xlsx file
        excel.ix[excel.Name == 'Patrick Talbot - Set Free Me', 'Name'] = (
            'Patrick Talbot - Set Me Free')

        # relative paths to each song
        mix_paths = ['Mixtures/Dev/' + _
                     for _ in sorted(os.listdir(
                        os.path.join(base_path, 'Mixtures/Dev')))]

        mix_paths += ['Mixtures/Test/' + _
                      for _ in sorted(os.listdir(
                            os.path.join(base_path, 'Mixtures/Test')))]

        source_paths = [_.replace('Mixtures', 'Sources') for _ in mix_paths]
        test_set = [0] * 50 + [1] * 50

        for row in excel.iterrows():

            artist_title = row[1]['Name']
            artist, title = artist_title.split(' - ')
            style = row[1]['Style']
            idx = [i for i, _ in enumerate(mix_paths) if artist_title in _][0]

            audio = {}
            audio['mixture'] = mix_paths[idx] + '/mixture.wav'

            for key in ['bass', 'drums', 'vocals', 'other']:
                audio[key] = '{0}/{1}.wav'.format(source_paths[idx], key)

            self.add_song(artist,
                          title,
                          style,
                          audio,
                          test_set=test_set[idx])


class MSD100(DSD100):

    def __init__(self,
                 base_path='/vol/vssp/datasets/audio/MSD100',
                 xlsx_name='msd100.xlsx'):
        super(MSD100, self).__init__(base_path, xlsx_name)
