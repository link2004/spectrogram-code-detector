import numpy as np
from scipy.io import wavfile
import time

#bpskの01埋め込みデータから位相の01に変換するアルゴリズム
#例：00110100010→000100111100
def binary_to_bpsk_phase(binary_message):
    phase_data = "0"
    tmp_bit = 0
    
    for bit in binary_message:
        tmp_bit = tmp_bit ^ int(bit)
        phase_data += str(tmp_bit)
    
    return phase_data

def generate_phase_shifting_sine(frequency, sample_rate, switch_interval, binary_message, output_file):
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

    # WAVファイルとして出力
    wavfile.write(output_file, sample_rate, audio)
    print(f"\n音声データをWAVファイル '{output_file}' として保存しました")
    
    print("\n=== 位相シフトサイン波の生成が完了しました ===\n")

def main():
    """
    メイン関数：位相シフトサイン波生成のデモンストレーション
    """
    # パラメータの設定
    frequency = 880  # 周波数 (Hz)
    sample_rate = 16000  # サンプリングレート (Hz)
    switch_interval = 32  # 位相反転間隔 (周期数)
    binary_message = "01010011"  # 埋め込むメッセージ
    output_file = f"wav/phase_shifting_sine_{frequency}Hz_{switch_interval}cycles.wav"  # 出力ファイル名

    print(f"パラメータ設定:\n周波数: {frequency}Hz\nサンプリングレート: {sample_rate}Hz\n位相反転間隔: {switch_interval}周期\nメッセージ: '{binary_message}'\n出力ファイル: {output_file}")

    # 位相シフトサイン波の生成と保存
    generate_phase_shifting_sine(frequency, sample_rate, switch_interval, binary_message, output_file)
    
    print(f"メッセージ '{binary_message}' を埋め込んだ位相シフトサイン波を {output_file} に生成しました。")

if __name__ == "__main__":
    main()