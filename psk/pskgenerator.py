import numpy as np
from scipy.io import wavfile

def generate_phase_shifting_sine(frequency, sample_rate, switch_interval, message, output_file):
    """
    位相を定期的に反転させるsin波の音を生成し、メッセージを埋め込んでWAVファイルとして出力する関数

    :param frequency: 音の周波数（Hz）
    :param sample_rate: サンプリングレート（Hz）
    :param switch_interval: 位相を反転させる間隔（周期数）
    :param message: 埋め込むメッセージ文字列
    :param output_file: 出力するWAVファイルの名前
    """
    print("=== 位相シフトサイン波の生成を開始します ===")
    
    # メッセージを2進数に変換
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    print(f"ステップ1: メッセージ '{message}' を2進数に変換しました")
    print(f"2進数メッセージ: {binary_message}")
    
    # 必要な時間を計算
    bits_count = len(binary_message)
    samples_per_bit = sample_rate * switch_interval / frequency
    total_samples = int(samples_per_bit * bits_count)
    duration = total_samples / sample_rate
    print(f"\nステップ2: 音声データの長さを計算しました")
    print(f"総ビット数: {bits_count}")
    print(f"1ビットあたりのサンプル数: {samples_per_bit:.2f}")
    print(f"総サンプル数: {total_samples}")
    print(f"音声の長さ: {duration:.2f}秒")

    # 時間配列を生成
    t = np.linspace(0, duration, total_samples, endpoint=False)
    print("\nステップ3: 時間軸を生成しました")

    # 基本のsin波を生成
    sine_wave = np.sin(2 * np.pi * frequency * t)
    print(f"\nステップ4: {frequency}Hzの基本のsin波を生成しました")

    # 位相反転のマスクを生成
    mask = np.ones_like(sine_wave)
    for i, bit in enumerate(binary_message):
        if bit == '1':
            start = int(i * samples_per_bit)
            end = int((i + 1) * samples_per_bit)
            mask[start:end] = -1
    print("\nステップ5: 2進数メッセージに基づいて位相反転のマスクを生成しました")
    print("'1'のビットに対応する部分で位相を反転させます")

    # 位相反転を適用
    phase_shifting_sine = sine_wave * mask
    print("\nステップ6: 基本のsin波に位相反転を適用しました")

    # 音量を正規化 (-1 to 1)
    phase_shifting_sine = phase_shifting_sine / np.max(np.abs(phase_shifting_sine))
    print("\nステップ7: 音量を-1から1の範囲に正規化しました")

    # 16ビット整数に変換
    audio = (phase_shifting_sine * 32767).astype(np.int16)
    print("\nステップ8: 音声データを16ビット整数に変換しました")

    # WAVファイルとして出力
    wavfile.write(output_file, sample_rate, audio)
    print(f"\nステップ9: 音声データをWAVファイル '{output_file}' として保存しました")
    
    print("\n=== 位相シフトサイン波の生成が完了しました ===")

def main():
    """
    メイン関数：位相シフトサイン波生成のデモンストレーション
    """
    # パラメータの設定
    frequency = 440  # 周波数 (Hz)
    sample_rate = 44100  # サンプリングレート (Hz)
    switch_interval = 16  # 位相反転間隔 (周期数)
    message = "hello"  # 埋め込むメッセージ
    output_file = f"phase_shifting_sine_{frequency}Hz_{switch_interval}cycles.wav"  # 出力ファイル名

    print(f"パラメータ設定:\n周波数: {frequency}Hz\nサンプリングレート: {sample_rate}Hz\n位相反転間隔: {switch_interval}周期\nメッセージ: '{message}'\n出力ファイル: {output_file}")

    # 位相シフトサイン波の生成と保存
    generate_phase_shifting_sine(frequency, sample_rate, switch_interval, message, output_file)
    
    print(f"メッセージ '{message}' を埋め込んだ位相シフトサイン波を {output_file} に生成しました。")

if __name__ == "__main__":
    main()