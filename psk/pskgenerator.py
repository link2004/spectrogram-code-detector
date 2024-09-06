import numpy as np
from scipy.io import wavfile

def generate_phase_shifting_sine(frequency, duration, sample_rate, switch_interval, output_file):
    """
    位相を定期的に反転させるsin波の音を生成し、WAVファイルとして出力する関数

    :param frequency: 音の周波数（Hz）
    :param duration: 音の長さ（秒）
    :param sample_rate: サンプリングレート（Hz）
    :param switch_interval: 位相を反転させる間隔（周期数）
    :param output_file: 出力するWAVファイルの名前
    """
    # 時間配列を生成
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 基本のsin波を生成
    sine_wave = np.sin(2 * np.pi * frequency * t)

    # 位相反転のマスクを生成
    samples_per_cycle = sample_rate / frequency
    samples_per_switch = samples_per_cycle * switch_interval
    num_switches = int(np.floor(len(sine_wave) / samples_per_switch))
    mask = np.ones_like(sine_wave)
    for i in range(num_switches):
        if i % 2 == 1:  # 奇数回目の区間で位相を反転
            start = int(i * samples_per_switch)
            end = int((i + 1) * samples_per_switch)
            mask[start:end] = -1

    # 位相反転を適用
    phase_shifting_sine = sine_wave * mask

    # 音量を正規化 (-1 to 1)
    phase_shifting_sine = phase_shifting_sine / np.max(np.abs(phase_shifting_sine))

    # 16ビット整数に変換
    audio = (phase_shifting_sine * 32767).astype(np.int16)

    # WAVファイルとして出力
    wavfile.write(output_file, sample_rate, audio)

# 使用例
generate_phase_shifting_sine(frequency=440, duration=5, sample_rate=44100, switch_interval=16, output_file="phase_shifting_sine.wav")