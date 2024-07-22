"""
 @Author: Envision
 @Github: ElapsingDreams
 @Gitee: ElapsingDreams
 @Email: None
 @FileName: main.py
 @DateTime: 2024/3/8 18:41
 @SoftWare: PyCharm
"""

import os
import pathlib
# import threading
import warnings

import Musicreater
# import mido
import numpy as np

# import sounddevice as sd
# import soundfile as sf
from Musicreater import MM_INSTRUMENT_DEVIATION_TABLE
from librosa import load as librosa_load
from librosa import resample as librosa_resample
from librosa.effects import pitch_shift as librosa_effects_pitch_shift
from librosa.effects import time_stretch as librosa_effects_time_stretch

# from MusicPreview.classes import MusicSequenceRepair

# from .constants import MM_DISLINK_PITCHED_INSTRUMENT_TABLE, MM_DISLINK_PERCUSSION_INSTRUMENT_TABLE, MM_HARP_PITCHED_INSTRUMENT_TABLE, MM_HARP_PERCUSSION_INSTRUMENT_TABLE

PATH = pathlib.Path(__file__)
# 我寻思着ASSETS直接内置咯
ASSETS_PATH = PATH.parent / "assets" / "wav"

"""已弃用"""
'''
INSTRUMENT_OFFSET_POS_TABLE: Dict[str, int] = {
    "note.harp": 66,  #
    "note.pling": 66,
    "note.guitar": 54,  #
    "note.iron_xylophone": 66,  #
    "note.bell": 90,  #
    "note.xylophone": 90,  #
    "note.chime": 90,  #
    "note.banjo": 66,
    "note.flute": 78,  #
    "note.bass": 42,  #
    "note.snare": 0,  # #
    "note.didgeridoo": 42,  #
    "mob.zombie.wood": 0,  # #
    "note.bit": 66,
    "note.hat": 0,  # #
    "note.bd": 0,  # #
    "note.basedrum": 0,  # #
    "firework.blast": 0,  # #
    "firework.twinkle": 0,  # #
    "fire.ignite": 0,  # #
    "note.cow_bell": 66,
}
"""不同乐器的音调偏离对照表"""
'''


class PreviewMusic:
    """
    将Midi转为音频之参数

    :param usr_input_path: str 用户输入midi文件路径
    :param usr_output_path: str 用户输入音频文件输出路径
    :param mode: bool 是否依照中文wiki定义：pitch即 播放速度 比 新播放速度
    :param out_sr: int 输出音频采样率，即质量
    """

    def __init__(
        self,
        musicsq: Musicreater.MusicSequence,
        mode: int = 0,
        gvm: int = 0,
        out_sr: int = 44100,
        overlay_channels: int = 1,
        default_channel_num: int = 1,
    ):
        # mode:
        # 0-OriginLength
        # 1-use_mc_player_define
        # 2-matchMIDI-cut
        # 3-matchMixing
        # 4-matchMIDI-TSM

        if (
            overlay_channels not in [1, 2]
            or default_channel_num not in [1, 2]
            or mode not in [0, 1, 2, 3, 4]
        ):
            raise ValueError("Illegal Value.")

        self.music_seq = musicsq

        self.in_path = None
        self.out_path = None
        self.mode = mode
        self.out_sr = out_sr
        self.gvm = gvm
        self.assets_dict = {}
        self.cache_dict = {}
        self.oc = overlay_channels
        self.dc = default_channel_num
        self.dev_list = self.__init_midi__()

        # self.dev_list = self.__init_midi__()

        # 预读取
        self.__int_read_assets()

        # 预生成
        self.__init_cache()

    def __init_midi__(self):
        # MusicSequence return: Tuple[Mapping[int, List[MineNote]], int, Dict[str, int], Dict[str, int]]
        # List[List[  str[sound_ID] int[midi_note_pitch] int[mc_tick_pos注意是多少tick《位置》执行]  ]]
        """ii = 1
        for i in [i for j in Musicreater.MusicSequence.to_music_note_channels(
                    mido.MidiFile(
                        self.in_path,
                        clip=True,
                    ),
                )[0].values() for i in j]:
            print(f"{i.sound_name}\t{i.note_pitch - 60 - MM_INSTRUMENT_DEVIATION_TABLE.get(i.sound_name, 6) if not i.percussive else None}\t{i.note_pitch - INSTRUMENT_OFFSET_POS_TABLE[i.sound_name] if not i.percussive else None}")
        """
        return sorted(
            (
                (
                    i.sound_name,
                    (
                        i.note_pitch
                        - 60
                        - MM_INSTRUMENT_DEVIATION_TABLE.get(i.sound_name, 6)
                        if not i.percussive
                        else None
                    ),
                    i.start_tick,
                    i.velocity / 127,
                    i.duration,
                )
                for i in sorted(
                    [i for j in self.music_seq.channels.values() for i in j],
                    key=lambda note: note.start_tick,
                )
            ),
            key=lambda x: x[2],
        )


    def __int_read_assets(self):
        files = [os.path.join(ASSETS_PATH, file) for file in os.listdir(ASSETS_PATH)]
        for file in files:
            self.assets_dict[os.path.split(file)[1].rsplit(".wav", 1)[0]] = (
                librosa_load(file, sr=None)
            )

    def __init_cache(self):
        # print(self.dev_list)
        for item in set(
            [(ii[0], ii[1], ii[4]) for ii in self.dev_list]
        ):  # 初始化音频数据 set( List[List[  str[sound_ID] int[midi_note_pitch] int[mc_tick_delay注意是多少tick《位置》执行]  ]])
            y_orig, sr_orig = self.assets_dict[item[0]]
            if self.oc == 2 and len(y_orig.shape) == 1:
                warnings.warn("Meaningless")
                y_orig = np.array([y_orig, y_orig])
                # print(y_orig)
            elif self.oc == 1 and len(y_orig.shape) == 2:
                y_orig = np.array(y_orig[self.dc])

            if item[1]:  # 适配打击乐
                # n_step = item[1] - INSTRUMENT_OFFSET_POS_TABLE[item[0]]
                # n_step = item[1]
                # times = 2 ** (item[1] / 12)
                raw_name = item[0] + "." + str(item[1])
                if self.mode == 1:
                    # 变调， 时域压扩， 重采样 mc方法
                    self.cache_dict[raw_name] = librosa_resample(
                        librosa_effects_time_stretch(
                            librosa_effects_pitch_shift(
                                y_orig, sr=sr_orig, n_steps=item[1]
                            ),
                            rate=2 ** (item[1] / 12),
                        ),
                        orig_sr=sr_orig,
                        target_sr=self.out_sr,
                        fix=False,
                    )
                elif self.mode == 0:
                    # 重采样， 变调
                    self.cache_dict[raw_name] = librosa_resample(
                        librosa_effects_pitch_shift(
                            y_orig, sr=sr_orig, n_steps=item[1]
                        ),
                        orig_sr=sr_orig,
                        target_sr=self.out_sr,
                        fix=False,
                    )
                elif self.mode == 4:

                    # 变调， 时域压扩， 重采样 MIDI-FFT
                    if self.oc == 2:
                        rate = item[2] / 20 / (len(y_orig[0]) / sr_orig)
                        rate = rate if rate != 0 else 1
                        self.cache_dict[raw_name] = librosa_resample(
                            librosa_effects_time_stretch(
                                librosa_effects_pitch_shift(
                                    y_orig, sr=sr_orig, n_steps=item[1]
                                ),
                                rate=rate,
                            ),
                            orig_sr=sr_orig,
                            target_sr=self.out_sr,
                            fix=False,
                        )
                    else:
                        rate = item[2] / 20 / (len(y_orig) / sr_orig)
                        rate = rate if rate != 0 else 1
                        self.cache_dict[raw_name] = librosa_resample(
                            librosa_effects_time_stretch(
                                librosa_effects_pitch_shift(
                                    y_orig, sr=sr_orig, n_steps=item[1]
                                ),
                                rate=rate,
                            ),
                            orig_sr=sr_orig,
                            target_sr=self.out_sr,
                            fix=False,
                        )
                elif self.mode == 2:
                    # 变调， 时域压扩， 重采样 MIDI-cut
                    if self.oc == 2:
                        deal = librosa_effects_pitch_shift(
                            y_orig, sr=sr_orig, n_steps=item[1]
                        )[
                            ...,
                            : (
                                int(item[2] / 20 * sr_orig)
                                if item[2] / 20 * sr_orig > len(y_orig[0])
                                else len(y_orig[0])
                            ),
                        ]
                    else:
                        deal = librosa_effects_pitch_shift(
                            y_orig, sr=sr_orig, n_steps=item[1]
                        )[
                            : (
                                int(item[2] / 20 * sr_orig)
                                if item[2] / 20 * sr_orig > len(y_orig)
                                else len(y_orig)
                            )
                        ]
                    self.cache_dict[raw_name] = librosa_resample(
                        deal, orig_sr=sr_orig, target_sr=self.out_sr, fix=False
                    )
            else:
                raw_name = item[0]
                # if self.mode == 1:
                # 重采样, 不变调
                self.cache_dict[raw_name] = librosa_resample(
                    y_orig, orig_sr=sr_orig, target_sr=self.out_sr, fix=False
                )
                """
                elif self.mode == 0:
                    # 重采样, 不变调, 衰弱
                    self.cache_dict[raw_name] = librosa_resample(
                        y_orig,
                        orig_sr=sr_orig,
                        target_sr=self.out_sr,
                        fix=False
                    )
                """
        del self.assets_dict

    def to_wav(self) -> np.ndarray:
        # 这玩意，真的太离谱。。虽然早考虑到这个问题，但在眼皮子底下我都没想着去改（）
        # 真的 我盯着这玩意想了大半个小时
        # 我 是 __ __
        # 遍历一次devlist，当前位置采样长度+对应音频采样长度 组成数组，找最大
        # len(self.cache_dict[(self.dev_list[i-1][0] + "." + str(
        #                 self.dev_list[i-1][1] - INSTRUMENT_OFFSET_POS_TABLE[self.dev_list[i-1][0]])) if self.dev_list[i-1][1] else
        #             self.dev_list[i-1][0]])
        # max_duration = int(max([(i[2] * 0.05 * self.out_sr + len((self.cache_dict[i[0] + "." + str(i[1] - INSTRUMENT_OFFSET_POS_TABLE[i[0]])]) if i[1] else self.cache_dict[i[0]])) for i in self.dev_list]))
        # wav_model = np.zeros(max_duration, dtype=np.float32)
        # - INSTRUMENT_OFFSET_POS_TABLE[i[0]]
        if self.oc == 1:

            def overlay(seg_overlay: np.ndarray, pos_tick: int):
                pos_ = int(out_sr * pos_tick * 0.05)
                # print(pos_, seg_overlay.size, wav_model.size, wav_model[pos_:seg_overlay.size + pos_].size, seg_overlay.dtype)
                wav_model[pos_ : seg_overlay.size + pos_] += seg_overlay

            wav_model = np.zeros(
                int(
                    max(
                        [
                            (
                                i[2] * 0.05 * self.out_sr
                                + len(
                                    (self.cache_dict[i[0] + "." + str(i[1])])
                                    if i[1]
                                    else self.cache_dict[i[0]]
                                )
                            )
                            for i in self.dev_list
                        ]
                    )
                ),
                dtype=np.float32,
            )
        elif self.oc == 2:

            def overlay(seg_overlay: np.ndarray, pos_tick: int):
                pos_ = int(out_sr * pos_tick * 0.05)
                # print(pos_, seg_overlay.size, wav_model.size, wav_model[pos_:seg_overlay.size + pos_].size, seg_overlay.dtype)
                wav_model[..., pos_ : len(seg_overlay[0]) + pos_] += seg_overlay

            wav_model = np.zeros(
                (
                    2,
                    int(
                        max(
                            [
                                (
                                    i[2] * 0.05 * self.out_sr
                                    + len(
                                        (self.cache_dict[i[0] + "." + str(i[1])][0])
                                        if i[1]
                                        else self.cache_dict[i[0]]
                                    )
                                )
                                for i in self.dev_list
                            ]
                        )
                    ),
                ),
                dtype=np.float32,
            )
        else:
            raise ValueError("illegal overlay_mode")

        out_sr = self.out_sr

        i = 0

        for item in self.dev_list:
            if item[1]:  # 适配打击乐
                # n_step = item[1] - INSTRUMENT_OFFSET_POS_TABLE[item[0]]
                raw_name = item[0] + "." + str(item[1])
                # print(self.cache_dict[raw_name].shape, "\n")
                overlay(self.cache_dict[raw_name] * item[3], item[2])

            else:
                raw_name = item[0]
                # print(self.cache_dict[raw_name].shape, "\n")
                overlay(self.cache_dict[raw_name] * item[3], item[2])
            # print(self.dev_list[-1][1] ,self.dev_list[-1][0])
            i += 1
            # print(i, len(self.dev_list))
        if self.gvm == 0:
            # 归一化，抚摸耳朵 (bushi
            max_val = np.max(np.abs(wav_model))
            if not max_val == 0:
                wav_model = wav_model / max_val
        elif self.gvm == 1:
            wav_model[wav_model > 1] = 1
            wav_model[wav_model < -1] = -1
        if self.oc == 2:
            return wav_model.T
        else:
            return wav_model[:, np.newaxis]

    # # 请使用本函数进行导出
    # def to_wav_file(self, out_file_path):
    #     sf.write(
    #         out_file_path,
    #         self.to_wav(),
    #         samplerate=self.out_sr,
    #         format="wav",
    #     )

    # def play(self):
    #     event = threading.Event()
    #     data, fs = self.to_wav(), self.out_sr
    #     if self.oc == 1:
    #         data = data[:, np.newaxis]

    #     self.current_frame = 0

    #     def callback(outdata, frames, time, status):  # CALLBACK need
    #         if status:
    #             print(status)
    #         chunksize = min(len(data) - self.current_frame, frames)
    #         outdata[:chunksize] = data[self.current_frame:self.current_frame + chunksize]
    #         if chunksize < frames:
    #             outdata[chunksize:] = 0
    #             raise sd.CallbackStop()
    #         self.current_frame += chunksize

    #     stream = sd.OutputStream(
    #         samplerate=fs, device=None, channels=self.oc,
    #         callback=callback, finished_callback=event.set)
    #     with stream:
    #         event.wait()  # Wait until playback is finished

    # @staticmethod
    # def _to_rel_mctick(messages):
    #     rel_messages = []
    #     now = 0
    #     for msg in messages:
    #         delta = msg[2] - now
    #         rel_messages.append((msg[0], msg[1], delta, msg[3], msg[4]))
    #         now = msg[2]
    #     return rel_messages

    # def stream(self):
    #     event = threading.Event()
    #     self.end = int(self.out_sr * self.dev_list[-1][2] * 0.05)
    #     self.current_frame = 0
    #     self.pos = 0
    #     if self.oc == 1:
    #         def overlay(seg_overlay: np.ndarray, pos_tick: int):
    #             pos_ = int(self.out_sr * pos_tick * 0.05)
    #             # print(pos_, seg_overlay.size, wav_model.size, wav_model[pos_:seg_overlay.size + pos_].size, seg_overlay.dtype)
    #             wav_model[pos_:seg_overlay.size + pos_] += seg_overlay

    #         wav_model = np.zeros(int(max([(i[2] * 0.05 * self.out_sr +
    #                                        len((self.cache_dict[i[0] + "." + str(i[1])])
    #                                            if i[1] else self.cache_dict[i[0]])) for i in self.dev_list])),
    #                              dtype=np.float32)
    #     elif self.oc == 2:
    #         def overlay(seg_overlay: np.ndarray, pos_tick: int):
    #             pos_ = int(self.out_sr * pos_tick * 0.05)
    #             # print(pos_, seg_overlay.size, wav_model.size, wav_model[pos_:seg_overlay.size + pos_].size, seg_overlay.dtype)
    #             wav_model[..., pos_:len(seg_overlay[0]) + pos_] += seg_overlay
    #             wav_model[wav_model > 1] = 1
    #             wav_model[wav_model < -1] = -1

    #         wav_model = np.zeros((2, int(max([(i[2] * 0.05 * self.out_sr +
    #                                            len((self.cache_dict[i[0] + "." + str(i[1])][0])
    #                                                if i[1] else self.cache_dict[i[0]])) for i in self.dev_list]))),
    #                              dtype=np.float32)
    #     else:
    #         raise ValueError("illegal overlay_mode")

    #     i = 0

    #     def callback(outdata, frames, _, status):  # CALLBACK need

    #         if status:
    #             print(status)

    #         chunksize = min(len(wav_model) - self.current_frame, frames)

    #         if self.pos < self.current_frame + chunksize and self.pos < self.end:
    #             outdata[:] = 0
    #         else:
    #             if self.oc == 1:
    #                 outdata[:chunksize] = wav_model[:, np.newaxis][self.current_frame:self.current_frame + chunksize]
    #             else:
    #                 outdata[:chunksize] = wav_model[self.current_frame:self.current_frame + chunksize]
    #             if chunksize < frames:
    #                 outdata[chunksize:] = 0
    #                 raise sd.CallbackStop()
    #             self.current_frame += chunksize

    #     stream = sd.OutputStream(
    #         samplerate=self.out_sr, device=None, channels=self.oc,
    #         callback=callback, finished_callback=event.set)

    #     with stream:
    #         for item in self.dev_list:
    #             self.pos = int(self.out_sr * item[2] * 0.05)
    #             if item[1]:  # 适配打击乐
    #                 # n_step = item[1] - INSTRUMENT_OFFSET_POS_TABLE[item[0]]
    #                 raw_name = item[0] + "." + str(item[1])
    #                 # print(self.cache_dict[raw_name].shape, "\n")
    #                 overlay(self.cache_dict[raw_name] * item[3], item[2])

    #             else:
    #                 raw_name = item[0]
    #                 # print(self.cache_dict[raw_name].shape, "\n")
    #                 overlay(self.cache_dict[raw_name] * item[3], item[2])
    #             # print(self.dev_list[-1][1] ,self.dev_list[-1][0])
    #             i += 1
    #             # print(i, len(self.dev_list))
    #         event.wait()  # Wait until playback is finished
