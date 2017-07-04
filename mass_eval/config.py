import pkg_resources
from collections import namedtuple

dsd_yaml = pkg_resources.resource_filename('mass_eval',
                                           'data/DSD100.yaml')

mus_csv = pkg_resources.resource_filename('mass_eval',
                                          'data/sisec_mus_2017_full.csv')

# User configurable:
mus_base_path = None
dsd_base_path = None
fs = 44100
audio_encoding = 'float32'


# Configuration of the MUSHRA mixing listening test.
# 
# For every question defined in the config section a single xml file will be
# generated containing the configuration in a format suitable for the
# WebAudioEvalutionTool [1].
# 
# [1] https://github.com/BrechtDeMan/WebAudioEvaluationTool
mushra = namedtuple('mushra', [])
# Name of listening test. The generated config files will be named:
# ${testname}_${question_id}.xml
mushra.testname = 'remix'
mushra.metric = [
    'testTimer',
    'elementTimer',
    'elementInitialPosition',
    'elementTracker',
    'elementFlagListenedTo',
    'elementFlagMoved',
    'elementListenTracker',
]
mushra.interface = [
    {'type': 'check', 'name': 'fragmentMoved'},
    {'type': 'check', 'name': 'scalerange', 'min': '25', 'max': '75'},
    {'type': 'show', 'name': 'fragmentSort'},
    {'type': 'show', 'name': 'playhead'},
    {'type': 'show', 'name': 'page-count'},
    {'type': 'show', 'name': 'volume'},
]
mushra.page = {
    'randomiseOrder': 'true',
    'synchronous': 'true',
    'repeatCount': '0',
    'loop': 'true',
    'loudness': '-23',
    'restrictMovement': 'true',
}
mushra.questions = {
    'part1':    {
        'title': 'Title of the first test',
        'description': ('Pop-up description of what to do in the first '
                        'test.'),
        'scale': {
            '0':   'The same',
            '100': 'Extremly different',
        },
    },
    'part2':  {
        'title': 'Title of the second test',
        'description': ('Pop-up description of what to do in the second ',
                        'test.'),
        'scale': {
            '0':   'Same quality',
            '100': 'Worse quality',
        },
    },
}
mushra.exit_message = 'Thank you for participating in this listening test!'
