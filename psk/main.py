from pskgenerator import generate_psk_signal
from pskdetector_pureData import main as detect_signal
from pskdetector_pureData import convert_wave_to_binary
import os
import random
def ensure_wav_directory():
    """wavディレクトリが存在しない場合は作成する"""
    if not os.path.exists('wav'):
        os.makedirs('wav')

def calculate_error_rate(original_message, detected_message):
    """誤り率を計算する"""
    # メッセージの長さが異なる場合は、短い方に合わせる
    min_length = min(len(original_message), len(detected_message))
    original = original_message[:min_length]
    detected = detected_message[:min_length]
    
    # 誤りの数をカウント
    errors = sum(1 for a, b in zip(original, detected) if a != b)
    
    # 誤り率を計算して返す
    return errors / min_length

def main():
    """PSK信号の生成と検出を行うメイン関数"""
    print("=== PSK信号の生成と検出を開始します ===\n")

    # 出力ファイルとパラメータの設定
    output_file = "wav/output.wav"
    sample_rate = 44100
    guard_band_width = 100
    # ランダムなバイナリメッセージを生成 (16ビット)
    # message = ''.join([str(random.randint(0, 1)) for _ in range(10000)])  
    message = "010011"
    # 生成する信号のパラメータ
    # frequencyはサンプリングレートの1/4以下の約数にする
    waves = [
        {"frequency": 11025, "switch_interval": 10, "binary_message": message},
    ]

    # 検出用のパラメータ（生成時のパラメータと一致させる）
    detection_parameters = [
        {"frequency": param["frequency"], "switch_interval": param["switch_interval"]}
        for param in waves
    ]

    # wavディレクトリの確認
    ensure_wav_directory()

    # 信号の生成
    print("【信号生成フェーズ】")
    generate_psk_signal(output_file, sample_rate, waves)

    print("\n【信号検出フェーズ】")
    # 生成した信号の検出
    # detected_messages = detect_signal(output_file, guard_band_width, detection_parameters)
    detected_message = convert_wave_to_binary(output_file, detection_parameters[0]["frequency"], detection_parameters[0]["switch_interval"])
    # 誤り率
    error_rate = calculate_error_rate(message, detected_message)
    print(f"original_message: {message}")
    print(f"detected_message: {detected_message}")
    print(f"誤り率: {error_rate*100}%")

if __name__ == "__main__":
    main()
