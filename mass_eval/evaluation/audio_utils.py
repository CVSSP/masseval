import os
from untwist import data, transforms, utilities
import pandas as pd
import numpy as np
from generate_anchors import Anchor


def load_audio(df, col='filepath', force_mono=False, key_prepend='',
               start=None, end=None):

    if isinstance(df, pd.Series):
        df = df.to_frame()

    out = {}
    for item in df.iterrows():
        wav = data.audio.Wave.read(item[1][col])
        if force_mono:
            wav = wav.as_mono()

        if start and end:
            wav = segment(wav, start, end)

        key = '{0}-{1}'.format(key_prepend, item[0])
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


def write_mixture_from_track_sample(sample,
                                    ref_path,
                                    others_path,
                                    directory,
                                    force_mono=True,
                                    target_loudness=-23,
                                    mixing_levels=[-12, -6, 0, 6, 12]):

    # Iterate over the tracks and write audio out:
    for g_sample, g_ref, g_others in zip(sample.groupby('track_id'),
                                         ref_path.groupby('track_id'),
                                         others_path.groupby('track_id')):

        # Prepare saving of audio
        folder = '{0}-{1}-{2}'.format(
            'mix',
            g_sample[1].iloc[0]['track_id'],
            g_sample[1].iloc[0]['metric'])
        full_path = os.path.join(directory, folder)
        if not os.path.exists(full_path):
            os.makedirs(full_path)

        # Reference target
        ref = load_audio(g_ref[1], 'filepath', force_mono, 'ref')
        # Find portion of track to take
        (ref_key, ref_audio), = ref.items()
        start, end = find_active_portion(ref_audio, 7, 75)
        target = segment(ref_audio, start, end)

        # Reference other stems
        others = load_audio(g_others[1], 'filepath', force_mono, 'other',
                            start, end)
        accomp = sum(other for name, other in others.items())

        # Anchors
        anchor_creator = Anchor(target, list(others.values()))
        target_anchors = anchor_creator.create()
        anchor_creator = Anchor(accomp, list(others.values()))
        accomp_anchors = anchor_creator.create()

        distortion = getattr(target_anchors, 'Distortion')
        artefacts = getattr(target_anchors, 'Artefacts')
        target_anchor = artefacts + 0.5 * distortion
        target_anchor.loudness = target_loudness

        distortion = getattr(accomp_anchors, 'Distortion')
        artefacts = getattr(accomp_anchors, 'Artefacts')
        accomp_anchor = artefacts + 0.5 * distortion
        accomp_anchor.loudness = target_loudness

        # Reference and anchor mixes
        for level in mixing_levels:
            name = 'ref_mix_' + str(level) + 'dB'
            mix = utilities.conversion.db_to_amp(level) * target + accomp
            write_wav(mix, os.path.join(full_path, name + '.wav'),
                      target_loudness)
            name = 'anchor_quality_mix_' + str(level) + 'dB'
            mix = utilities.conversion.db_to_amp(level) * target_anchor \
                + accomp_anchor
            write_wav(mix, os.path.join(full_path, name + '.wav'),
                      target_loudness)
            name = 'anchor_level_mix_' + str(level) + 'dB'
            mix = utilities.conversion.db_to_amp(level - 14) \
                * target + accomp
            write_wav(mix, os.path.join(full_path, name + '.wav'),
                      target_loudness)

        # Mixes per method
        for method_name, method_sample in g_sample[1].groupby('method'):
            # Get vocals and accompaniment
            index = method_sample['target'] == 'vocals'
            vocals = load_audio(method_sample[index], 'filepath',
                                force_mono, 'vocals', start, end)
            index = method_sample['target'] == 'accompaniment'
            accompaniments = load_audio(method_sample[index], 'filepath',
                                        force_mono, 'accomp', start, end)
            # Mixing
            (_, vocal), = vocals.items()
            (_, accomp), = accompaniments.items()
            for level in mixing_levels:
                name = method_name + '_mix_' + str(level) + 'dB'

                mix = utilities.conversion.db_to_amp(level) * vocal + accomp
                write_wav(mix, os.path.join(full_path, name + '.wav'),
                          target_loudness)


def write_audio_from_track_sample(sample,
                                  ref_path,
                                  others_path,
                                  directory,
                                  force_mono=True,
                                  target_loudness=-23):

    # Iterate over the tracks and write audio out:
    for g_sample, g_ref, g_others in zip(sample.groupby('track_id'),
                                         ref_path.groupby('track_id'),
                                         others_path.groupby('track_id')):

        ref = load_audio(g_ref[1], 'filepath', force_mono, 'ref')

        # find portion of track to take
        (ref_key, ref_audio), = ref.items()
        start, end = find_active_portion(ref_audio, 7, 75)
        ref[ref_key] = segment(ref_audio, start, end)

        # Load test items at the same point in time (same segment times)
        test_items = load_audio(g_sample[1], 'filepath', force_mono, 'test',
                                start, end)

        # Ditto but for other stems
        others = load_audio(g_others[1], 'filepath', force_mono, 'other',
                            start, end)

        # Generate anchors
        anchor_creator = Anchor(ref[ref_key], list(others.values()))
        anchors = anchor_creator.create()

        # Write audio
        folder = '{0}-{1}-{2}'.format(
            g_sample[1].iloc[0]['target'],
            g_sample[1].iloc[0]['track_id'],
            g_sample[1].iloc[0]['metric'])

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
    # sig.astype('float32')
    sig.write(filename)
