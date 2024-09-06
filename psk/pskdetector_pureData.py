import numpy as np
from scipy.io import wavfile
from scipy import signal

# wavファイルを読み込む関数
def read_wav_file(file_path):
    sample_rate, audio = wavfile.read(file_path)
    return sample_rate, audio


def detect_phase_shifting_sine(audio, sample_rate, frequency, switch_interval):
    """
    位相シフトサイン波からメッセージを復調する関数

    :param input_file: 入力WAVファイルの名前
    :return: 復調されたメッセージ
    """
    print("=== 位相シフトサイン波の復調を開始します ===")

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

    # ディレイ音声データと元の音声データを足した音声データをファイルに出力
    # wavfile.write("mixed_audio.wav", sample_rate, mixed_audio)
    # wavfile.write("original_audio.wav", sample_rate, audio)
    # wavfile.write("delayed_audio.wav", sample_rate, delayed_audio)

    return ''.join(map(str, bit_data))

def detect_phase_shifting_sine_multiply(audio, sample_rate, frequency, switch_interval):
    """
    位相シフトサイン波からメッセージを復調する関数

    :param input_file: 入力WAVファイルの名前
    :return: 復調されたメッセージ
    """

    # 正規化
    audio = audio / np.max(audio)

    # 音声データを1bitデータ分ディレイ
    delay_samples = int(sample_rate * switch_interval / frequency)
    delayed_audio = np.roll(audio, delay_samples)

    # ディレイ音声データと元の音声データを掛け合わせる
    mixed_audio = np.multiply(audio, delayed_audio)

    # 1ビットデータ範囲ごとの和を計算
    bit_count = len(mixed_audio) // delay_samples
    bit_sums = np.array([np.sum(mixed_audio[i*delay_samples:(i+1)*delay_samples]) for i in range(bit_count)])

    # しきい値を設定して1ビットデータに変換
    threshold = np.mean([np.max(bit_sums), np.min(bit_sums)])
    bit_data = (bit_sums <= threshold).astype(int)[1:]

    # ディレイ音声データと元の音声データを足した音声データをファイルに出力
    # wavfile.write("mixed_audio.wav", sample_rate, mixed_audio)
    # wavfile.write("original_audio.wav", sample_rate, audio)
    # wavfile.write("delayed_audio.wav", sample_rate, delayed_audio)

    return ''.join(map(str, bit_data))


def bandpass_filter(audio, sample_rate, center_freq, guard_band_width):
    """
    帯域通過フィルタを適用し、指定された帯域のみを出力する関数

    :param input_file: 入力音声ファイルのパス
    :param center_freq: 中心周波数 (Hz)
    :param guard_band_width: ガードバンドの幅 (Hz)
    :return: フィルタリングされた音声データのnumpy配列
    """
    print(f"=== 帯域通過フィルタの適用を開始します ===")
    print(f"中心周波数: {center_freq} Hz")
    print(f"ガードバンド幅: {guard_band_width} Hz")

    # フィルタのパラメータを計算
    nyquist_freq = 0.5 * sample_rate
    low_cut = (center_freq - guard_band_width / 2) / nyquist_freq
    high_cut = (center_freq + guard_band_width / 2) / nyquist_freq

    # バターワースフィルタを設計
    b, a = signal.butter(6, [low_cut, high_cut], btype='band')

    # フィルタを適用
    filtered_audio = signal.filtfilt(b, a, audio)

    return filtered_audio



def main():
    """
    メイン関数：位相シフトサイン波復調のデモンストレーション
    """
    input_file = "440hz_and_880hz.wav"  # 入力ファイル名
    parameters = [
        {"frequency": 880, "switch_interval": 32, "center_freq": 880, "guard_band_width": 220},
        {"frequency": 440, "switch_interval": 16, "center_freq": 440, "guard_band_width": 220}
    ]

    print(f"入力ファイル: {input_file}")
    print("パラメータ設定:")
    for i, param in enumerate(parameters, 1):
        print(f"パラメータセット {i}:")
        print(f"  周波数: {param['frequency']}Hz")
        print(f"  位相反転間隔: {param['switch_interval']}周期")
        print(f"  中心周波数: {param['center_freq']}Hz")
        print(f"  ガードバンド幅: {param['guard_band_width']}Hz\n")

    # 音声データを読み込む
    sample_rate, audio = read_wav_file(input_file)

    for i, param in enumerate(parameters, 1):
        # フィルタリング
        filtered_audio = bandpass_filter(audio, sample_rate, param['center_freq'], param['guard_band_width'])

        # 位相シフトサイン波の復調
        detected_message = detect_phase_shifting_sine_multiply(filtered_audio, sample_rate, param['frequency'], param['switch_interval'])

        print(f"パラメータセット {i} の復調されたメッセージ: {detected_message}")

if __name__ == "__main__":
    main()
