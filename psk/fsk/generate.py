import numpy as np
from scipy.io import wavfile

# FSK変調のパラメータ設定
sample_rate = 44100  # サンプリングレート
duration = 0.001  # 1ビットあたりの時間(秒)
t = np.linspace(0, duration, int(sample_rate * duration))

# 入力バイナリ信号
# ランダムな10000桁のバイナリ信号を生成
binary_signal = ''.join(np.random.choice(['0', '1']) for _ in range(40))
# FSK変調の実装
modulated_signal = []
for bit in binary_signal:
    if bit == '1':
        # 1の場合は2000Hz（可聴域内）
        signal = np.sin(2 * np.pi * 20000 * t)
    else:
        # 0の場合は1000Hz（可聴域内）
        signal = np.sin(2 * np.pi * 19000 * t)
    modulated_signal.extend(signal)
    # 無音区間の追加
    silence = np.zeros(int(sample_rate * duration))
    modulated_signal.extend(silence)

# 信号を-1から1の範囲に正規化
modulated_signal = np.array(modulated_signal)
modulated_signal = modulated_signal / np.max(np.abs(modulated_signal))

# 16ビット整数に変換（-32768から32767の範囲）
modulated_signal = (modulated_signal * 32767).astype(np.int16)

# WAVファイルとして保存
wavfile.write('fsk_modulated.wav', sample_rate, modulated_signal)
