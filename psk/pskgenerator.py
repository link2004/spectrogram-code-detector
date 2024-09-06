import numpy as np
from scipy.io import wavfile
import time

def output_wav_file(audio, sample_rate, output_file):
    wavfile.write(output_file, sample_rate, audio)
    print(f"\n音声データをWAVファイル '{output_file}' として保存しました")


#bpskの01埋め込みデータから位相の01に変換するアルゴリズム
#例：00110100010→000100111100
def binary_to_bpsk_phase(binary_message):
    phase_data = "0"
    tmp_bit = 0
    
    for bit in binary_message:
        tmp_bit = tmp_bit ^ int(bit)
        phase_data += str(tmp_bit)
    
    return phase_data

def generate_phase_shifting_sine(frequency, sample_rate, switch_interval, binary_message):
    """
    位相を定期的に反転させるsin波の音を生成し、メッセージを埋め込んでWAVファイルとして出力する関数

    :param frequency: 音の周波数（Hz）
    :param sample_rate: サンプリングレート（Hz）
    :param switch_interval: 位相を反転させる間隔（周期数）
    :param message: 埋め込むメッセージ文字列
    :param output_file: 出力するWAVファイルの名前
    """
    print("\n=== 位相シフトサイン波の生成を開始します ===\n")

    # 位相の01に変換
    phase_mask = binary_to_bpsk_phase(binary_message)
    print(f"phase_mask: {phase_mask}\n")
    
    # 必要な時間を計算
    bits_count = len(phase_mask)
    samples_per_bit = sample_rate * switch_interval / frequency #1ビットを表すのに必要なサンプル数
    total_samples = int(samples_per_bit * bits_count) #総サンプル数
    duration = total_samples / sample_rate #音声の長さ
    print(f"総ビット数: {bits_count}")
    print(f"1ビットあたりのサンプル数: {samples_per_bit:.2f}")
    print(f"総サンプル数: {total_samples}")
    print(f"音声の長さ: {duration:.2f}秒")

    # 時間配列を生成
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # 基本のsin波を生成
    sine_wave = np.sin(2 * np.pi * frequency * t)

    # 位相反転のマスクを生成
    mask = np.ones_like(sine_wave)
    for i, bit in enumerate(phase_mask):
        if bit == '1':
            start = int(i * samples_per_bit)
            end = int((i + 1) * samples_per_bit)
            mask[start:end] = -1


    # 位相反転を適用
    phase_shifting_sine = sine_wave * mask

    # 音量を正規化 (-1 to 1)
    phase_shifting_sine = phase_shifting_sine / np.max(np.abs(phase_shifting_sine))

    # 16ビット整数に変換
    audio = (phase_shifting_sine * 32767).astype(np.int16)

    return audio

def combine_audio_signals(*audio_signals):
    """
    複数の音声データを合成する関数

    :param audio_signals: 合成する音声データのリスト（numpy配列）
    :return: 合成された音声データ（numpy配列）
    """
    print("\n=== 複数の音声データの合成を開始します ===\n")

    # 入力された音声データの数を確認
    num_signals = len(audio_signals)
    print(f"合成する音声データの数: {num_signals}")

    if num_signals == 0:
        print("警告: 合成する音声データがありません。")
        return np.array([])

    # すべての音声データの長さを確認
    lengths = [len(signal) for signal in audio_signals]
    max_length = max(lengths)
    print(f"最大の音声データ長: {max_length}")

    # 最大の長さに合わせて各音声データをパディング
    padded_signals = []
    for signal in audio_signals:
        if len(signal) < max_length:
            padded_signal = np.pad(signal, (0, max_length - len(signal)), 'constant')
        else:
            padded_signal = signal
        padded_signals.append(padded_signal)

    # すべての音声データを合成
    combined_signal = np.sum(padded_signals, axis=0)

    # 音量を正規化 (-32768 to 32767)
    max_amplitude = np.max(np.abs(combined_signal))
    if max_amplitude > 0:
        normalized_signal = (combined_signal / max_amplitude * 32767).astype(np.int16)
    else:
        normalized_signal = combined_signal.astype(np.int16)

    print(f"合成された音声データの長さ: {len(normalized_signal)}")
    print("音声データの合成が完了しました。")

    return normalized_signal

def main():
    """
    メイン関数：位相シフトサイン波生成のデモンストレーション
    """
    # パラメータの設定
    output_file = "wav/440hz_660hz_880hz_1100hz_test.wav"  # 出力ファイル名
    sample_rate = 16000  # サンプリングレート (Hz)
    
    parameters = [
        {"frequency": 440,  "switch_interval": 16, "binary_message": "00110101"},
        {"frequency": 660,  "switch_interval": 16, "binary_message": "011011010110"},
        {"frequency": 880,  "switch_interval": 16, "binary_message": "0011010100010101"},
        {"frequency": 1100, "switch_interval": 16, "binary_message": "010100111101011010010101"},
    ]

    print(f"パラメータ設定:")
    for i, param in enumerate(parameters, 1):
        print(f"パラメータセット {i}:")
        print(f"  周波数: {param['frequency']}Hz")
        print(f"  位相反転間隔: {param['switch_interval']}周期")
        print(f"  メッセージ: '{param['binary_message']}'")
    print(f"サンプリングレート: {sample_rate}Hz")
    print(f"出力ファイル: {output_file}")

    # 位相シフトサイン波の生成と保存
    audio_signals = []
    for param in parameters:
        frequency = param['frequency']
        switch_interval = param['switch_interval']
        binary_message = param['binary_message']
        audio = generate_phase_shifting_sine(frequency, sample_rate, switch_interval, binary_message)
        audio_signals.append(audio)
    
    combined_audio = combine_audio_signals(*audio_signals)
    
    # WAVファイルとして出力
    output_wav_file(combined_audio, sample_rate, output_file)

    print(f"複数のメッセージを埋め込んだ位相シフトサイン波を {output_file} に生成しました。")

if __name__ == "__main__":
    main()