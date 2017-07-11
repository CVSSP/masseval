from untwist import data
from masseval import anchor, audio

if __name__ == '__main__':

    paths = [
        ('/vol/vssp/datasets/audio/DSD100/Sources/Test/019 - '
         'James Elder & Mark M Thompson - The English Actor/vocals.wav'),
        ('/vol/vssp/datasets/audio/DSD100/Sources/Test/019 - '
         'James Elder & Mark M Thompson - The English Actor/drums.wav'),
        ('/vol/vssp/datasets/audio/DSD100/Sources/Test/019 - '
         'James Elder & Mark M Thompson - The English Actor/other.wav'),
        ('/vol/vssp/datasets/audio/DSD100/Sources/Test/019 - '
         'James Elder & Mark M Thompson - The English Actor/bass.wav'),
    ]

    target = data.audio.Wave.read(paths[0]).as_mono()
    others = [data.audio.Wave.read(paths[1]).as_mono(),
              data.audio.Wave.read(paths[2]).as_mono(),
              data.audio.Wave.read(paths[3]).as_mono()]

    trim_factor_distorted = 0.2
    trim_factor_artefacts = 0.99
    remix_anchor_target_level_offset = -14
    remix_anchor_distortion_artefacts_balance = [0, 0]

    print('Generating single source anchors...')
    creator = anchor.Anchor(target,
                            others,
                            trim_factor_distorted,
                            trim_factor_artefacts)

    anchors = creator.create()

    for name in anchors._fields:
        wav = getattr(anchors, name)
        audio.write_wav(wav, name + '.wav', target_loudness=-30)

    print('Generating remix anchors...')

    creator = anchor.RemixAnchor(target,
                                 others,
                                 trim_factor_distorted,
                                 trim_factor_artefacts,
                                 remix_anchor_target_level_offset,
                                 remix_anchor_distortion_artefacts_balance)

    anchors = creator.create()

    for name in anchors._fields:
        wav = getattr(anchors, name)
        audio.write_wav(wav, name + '_remix.wav', target_loudness=-30)
