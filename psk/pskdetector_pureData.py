import numpy as np
from scipy.io import wavfile

def detect_phase_shifting_sine(input_file, frequency, switch_interval):
    """
    位相シフトサイン波からメッセージを復調する関数

    :param input_file: 入力WAVファイルの名前
    :return: 復調されたメッセージ
    """
    print("=== 位相シフトサイン波の復調を開始します ===")

    # 音声データを読み込む
    sample_rate, audio = wavfile.read(input_file)
    print(f"サンプリングレート: {sample_rate}Hz")

    # 正規化
    audio = audio / np.max(audio)

    # 音声データを1bitデータ分ディレイ
    delay_samples = int(sample_rate * switch_interval / frequency)
    delayed_audio = np.roll(audio, delay_samples)

    # ディレイ音声データと元の音声データを足す
    mixed_audio = np.add(audio, delayed_audio)

    # 絶対値を取る
    mixed_audio = np.abs(mixed_audio)

    # 1ビットデータ範囲ごとの和を計算
    bit_count = len(mixed_audio) // delay_samples
    bit_sums = np.array([np.sum(mixed_audio[i*delay_samples:(i+1)*delay_samples]) for i in range(bit_count)])

    # しきい値を設定して1ビットデータに変換
    threshold = np.mean([np.max(bit_sums), np.min(bit_sums)])
    bit_data = (bit_sums <= threshold).astype(int)[1:]

    print("ビットデータ:", bit_data)
    # ディレイ音声データと元の音声データを足した音声データをファイルに出力
    # wavfile.write("mixed_audio.wav", sample_rate, mixed_audio)
    # wavfile.write("original_audio.wav", sample_rate, audio)
    # wavfile.write("delayed_audio.wav", sample_rate, delayed_audio)

    return ''.join(map(str, bit_data))

def main():
    """
    メイン関数：位相シフトサイン波復調のデモンストレーション
    """
    input_file = "phase_shifting_sine_440Hz_1cycles.wav"  # 入力ファイル名
    frequency = 440  # 周波数 (Hz)
    switch_interval = 1  # 位相反転間隔 (周期数)

    print(f"入力ファイル: {input_file}")
    print(f"パラメータ設定:\n周波数: {frequency}Hz\n位相反転間隔: {switch_interval}周期\n")

    # 位相シフトサイン波の復調
    detected_message = detect_phase_shifting_sine(input_file, frequency, switch_interval)
    
    print(f"復調されたメッセージ: '{detected_message}'")

if __name__ == "__main__":
    main()
