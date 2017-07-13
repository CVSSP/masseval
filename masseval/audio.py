import os

import pandas as pd
import numpy as np

from untwist import (data, transforms, utilities)

from . import anchor


def load_audio(df, force_mono=False, start=None, end=None):

    if isinstance(df, pd.Series):
        df = df.to_frame()

    out = {}
    for item in df.iterrows():
        wav = data.audio.Wave.read(item[1]['filepath'])
        if force_mono:
            wav = wav.as_mono()

        if start and end:
            wav = segment(wav, start, end)

        # key = '{0}-{1}'.format(key_prepend, item[1]['method'])
        key = '{0}-{1}'.format(item[1]['method'], item[1]['target'])
        out[key] = wav

    return out


def find_active_portion(wave, duration, perc=90):
    '''
    Returns the start and end sample indices of an active portion of the audio
    file according to the Pth percentile of the windowed energy measurements.
    '''

    window_size = int(np.round(wave.sample_rate * duration))
    hop_size = window_size // 4
    framer = transforms.stft.Framer(window_size, hop_size,
                                    False, False)
    frames = framer.process(wave.as_mono())
    energy = (frames * frames).mean(1)

    select_frame = np.argmin(np.abs(energy - np.percentile(energy, perc)))

    start = select_frame * hop_size
    end = start + window_size

    return start, end


def segment(wave, start, end, ramp_dur=0.02):

    wave = wave[start:end]

    ramp_dur_samples = int(np.round(ramp_dur * wave.sample_rate))

    t = np.linspace(0, np.pi / 2.0, ramp_dur_samples).reshape(-1, 1)
    wave[:ramp_dur_samples] *= np.sin(t) ** 2
    wave[-ramp_dur_samples:] *= np.cos(t) ** 2

    return wave


def write_mixtures_from_sample(sample,
                               target='vocals',
                               directory=None,
                               force_mono=True,
                               target_loudness=-23,
                               mixing_levels=[-12, -6, 0, 6, 12],
                               segment_duration=7):

    # Iterate over the tracks and write audio out:
    for idx, g_sample in sample.groupby('track_id'):

        # Prepare saving of audio
        folder = '{0}-{1}-{2}'.format(
            'mix',
            g_sample.iloc[0]['track_id'],
            g_sample.iloc[0]['metric'])

        full_path = os.path.join(directory, folder)

        if not os.path.exists(full_path):
            os.makedirs(full_path)

        '''
        Reference audio
        '''

        ref_sample = g_sample[g_sample.method == 'Ref']

        # Reference target
        ref = load_audio(ref_sample[ref_sample.target == target],
                         force_mono)

        # Find portion of track to take
        (ref_key, ref_audio), = ref.items()
        start, end = find_active_portion(ref_audio, segment_duration, 75)
        target_audio = segment(ref_audio, start, end)

        # Reference non-target stems
        others = load_audio(
            ref_sample[ref_sample.target != target],
            force_mono,
            start,
            end)
        accomp_audio = sum(other for name, other in others.items())

        # Reference and anchor mixes
        for level in mixing_levels:

            name = 'ref_mix_{}dB'.format(level)
            mix = (utilities.conversion.db_to_amp(level) * target_audio +
                   accomp_audio)
            write_wav(mix, os.path.join(full_path, name + '.wav'),
                      target_loudness)

            creator = anchor.RemixAnchor(
                    utilities.conversion.db_to_amp(level) * target_audio,
                    accomp_audio,
                    trim_factor_distorted=0.2,
                    trim_factor_artefacts=0.99,
                    target_level_offset=-14,
                    quality_anchor_loudness_balance=[0, 0])
            anchors = creator.create()
            for anchor_type in anchors._fields:
                if anchor_type == 'Interferer':
                    name = 'anchor_loudness_mix_{}dB'.format(level)
                elif anchor_type == 'Quality':
                    name = 'anchor_quality_mix_{}dB'.format(level)
                else:
                    continue
                wav = getattr(anchors, anchor_type)
                write_wav(wav,
                          os.path.join(full_path, name + '.wav'),
                          target_loudness)

        # Mixes per method
        not_ref_sample = g_sample[g_sample.method != 'Ref']
        for method_name, method_sample in not_ref_sample.groupby('method'):

            # Get target and accompaniment
            index = method_sample['target'] == target

            target_audio = load_audio(method_sample[index],
                                      force_mono, start, end)

            (_, target_audio), = target_audio.items()

            if 'accompaniment' in method_sample['target'].values:

                index = method_sample['target'] == 'accompaniment'

                accompaniments = load_audio(method_sample[index],
                                            force_mono, start, end)

                (_, accomp), = accompaniments.items()

            else:

                others = load_audio(
                    method_sample[method_sample.target != target],
                    force_mono,
                    start,
                    end)

                accomp = sum(other for name, other in others.items())

            # Fix GRA
            if method_name in ['GRA2', 'GRA3']:
                target_audio = -1 * target_audio
                accomp = -1 * accomp

            # Mixing
            for level in mixing_levels:
                name = '{0}_mix_{1}dB'.format(method_name, level)

                mix = (utilities.conversion.db_to_amp(level) * target_audio +
                       accomp)

                write_wav(mix, os.path.join(full_path, name + '.wav'),
                          target_loudness)


def write_target_from_sample(sample,
                             target='vocals',
                             directory=None,
                             force_mono=True,
                             target_loudness=-23,
                             segment_duration=7):

    # Iterate over the tracks and write audio out:
    for idx, g_sample in sample.groupby('track_id'):

        ref_sample = g_sample[g_sample.method == 'Ref']

        # Reference target
        ref = load_audio(ref_sample[ref_sample.target == target],
                         force_mono)

        # Find portion of track to take
        (ref_key, ref_audio), = ref.items()
        start, end = find_active_portion(ref_audio, segment_duration, 75)
        ref[ref_key] = segment(ref_audio, start, end)

        # Reference non-target stems
        others = load_audio(ref_sample[ref_sample.target != target],
                            force_mono,
                            start,
                            end)

        # Load test items at the same point in time (same segment times)
        test_items = load_audio(g_sample[(g_sample.method != 'Ref') &
                                         (g_sample.target == target)],
                                force_mono,
                                start,
                                end)

        # Generate anchors
        anchor_creator = anchor.Anchor(ref[ref_key],
                                       list(others.values()))
        anchors = anchor_creator.create()

        # Write audio
        folder = '{0}-{1}-{2}'.format(
            target,
            g_sample.iloc[0]['track_id'],
            g_sample.iloc[0]['metric'])

        full_path = os.path.join(directory, folder)

        if not os.path.exists(full_path):
            os.makedirs(full_path)

        for name, wav in ref.items():
            write_wav(wav, os.path.join(full_path, name + '.wav'),
                      target_loudness)

        for name, wav in test_items.items():
            write_wav(wav, os.path.join(full_path, name + '.wav'),
                      target_loudness)

        for name in anchors._fields:
            wav = getattr(anchors, name)
            write_wav(wav, os.path.join(full_path, name + '.wav'),
                      target_loudness)


def write_wav(sig, filename, target_loudness=-23):
    sig.loudness = target_loudness
    # If you need 32-bit wavs, use
    sig = sig.astype('float32')
    sig.write(filename)


def combine_anchors(distortion, artefact):
    gain = utilities.conversion.db_to_amp(
        distortion.loudness - artefact.loudness)
    return 0.7 * distortion + 0.3 * gain * artefact
