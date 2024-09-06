import numpy as np
from scipy.io import wavfile
from scipy.signal import hilbert

def psk_demodulate_wav(file_path, frequency, cycles_per_symbol):
    """
    WAVファイルからPSK変調された信号を復調する関数

    :param file_path: 入力WAVファイルのパス
    :param frequency: 搬送波の周波数 (Hz)
    :param cycles_per_symbol: 1シンボルあたりの搬送波の周期数
    :return: 復調されたビット列
    """
    # WAVファイルを読み込む
    sample_rate, audio_data = wavfile.read(file_path)
    
    # ステレオの場合は最初のチャンネルのみを使用
    if audio_data.ndim > 1:
        audio_data = audio_data[:, 0]
    
    # 音声データを-1から1の範囲に正規化
    audio_data = audio_data.astype(float) / np.max(np.abs(audio_data))

    # 解析信号を生成（ヒルベルト変換を使用）
    analytic_signal = hilbert(audio_data)

    # 位相を抽出
    instantaneous_phase = np.unwrap(np.angle(analytic_signal))

    # 1シンボルあたりのサンプル数を計算
    samples_per_symbol = int(sample_rate * cycles_per_symbol / frequency)

    # シンボルごとの位相差を計算
    phase_differences = np.diff(instantaneous_phase[::samples_per_symbol])

    # 位相差をビットに変換（閾値は0とする）
    demodulated_bits = (phase_differences > 0).astype(int)

    return demodulated_bits

def bits_to_text(bits):
    """
    ビット列をテキストに変換する関数

    :param bits: ビット列
    :return: 変換されたテキスト
    """
    # ビット列を8ビットずつのグループに分割
    byte_groups = [bits[i:i+8] for i in range(0, len(bits), 8)]
    
    # 各グループを文字に変換
    text = ''
    for group in byte_groups:
        if len(group) == 8:  # 8ビット未満のグループは無視
            char_code = int(''.join(map(str, group)), 2)
            text += chr(char_code)
    
    return text

def main():
    """
    メイン関数：PSK復調のデモンストレーション
    """
    # 入力ファイルのパス
    file_path = "./phase_shifting_sine_440Hz_16cycles.wav"
    
    # 搬送波の周波数 (Hz)
    frequency = 440
    
    # 1シンボルあたりの搬送波の周期数
    cycles_per_symbol = 16
    
    # PSK復調を実行
    demodulated_bits = psk_demodulate_wav(file_path, frequency, cycles_per_symbol)
    
    # 結果を表示
    print("復調されたビット列:")
    print(demodulated_bits)
    
    # ビット列を文字列に変換
    demodulated_text = bits_to_text(demodulated_bits)
    
    print("\n復調されたテキスト:")
    print(demodulated_text)

if __name__ == "__main__":
    main()
