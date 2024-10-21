import numpy as np
import sounddevice as sd

def play_sine_wave(frequency, duration, amplitude=1.0, sample_rate=44100):
    """
    サイン波の音を生成して再生する関数

    :param frequency: 周波数（Hz）
    :param duration: 再生時間（秒）
    :param amplitude: 振幅（0.0から1.0の間）
    :param sample_rate: サンプリングレート（Hz）
    """
    # 時間配列を生成
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # サイン波を生成
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)

    # 音を再生
    sd.play(sine_wave, sample_rate)
    sd.wait()
def play_chord(frequencies, duration, amplitude=1.0, sample_rate=44100):
    """
    複数の周波数を同時に再生して和音を作る関数

    :param frequencies: 周波数のリスト（Hz）
    :param duration: 再生時間（秒）
    :param amplitude: 振幅（0.0から1.0の間）
    :param sample_rate: サンプリングレート（Hz）
    """
    # 時間配列を生成
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 各周波数のサイン波を生成し、合成
    chord = np.zeros_like(t)
    for freq in frequencies:
        chord += amplitude * np.sin(2 * np.pi * freq * t)

    # 振幅を正規化
    chord /= len(frequencies)

    # クリッピングを防ぐためにノーマライズ
    max_amplitude = np.max(np.abs(chord))
    if max_amplitude > 1.0:
        chord = chord / max_amplitude

    # 音を再生
    sd.play(chord, sample_rate)
    sd.wait()

# 使用例
if __name__ == "__main__":
        # Cメジャーコードを再生（C5, E5, G5）
    c_major = [523.25, 659.25, 783.99]
    play_sine_wave(c_major[0], 2)  
    play_sine_wave(c_major[1], 2)
    play_sine_wave(c_major[2], 2)
    play_chord(c_major, 2)
