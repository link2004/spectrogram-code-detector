import numpy as np
from scipy.io import wavfile
import time
from typing import List, Dict

def save_wav_file(audio: np.ndarray, sample_rate: int, output_file: str) -> None:
    """WAVファイルとして音声データを保存する"""
    wavfile.write(output_file, sample_rate, audio)
    print(f"\n音声データをWAVファイル '{output_file}' として保存しました")

def binary_to_bpsk_phase(binary_message: str) -> str:
    """
    BPSKの01埋め込みデータから位相の01に変換する
    
    Args:
        binary_message: 変換する2進数メッセージ
    Returns:
        位相データを表す2進数文字列
    """
    phase_data = "0"
    tmp_bit = 0
    
    for bit in binary_message:
        tmp_bit = tmp_bit ^ int(bit)
        phase_data += str(tmp_bit)
    
    return phase_data

def calculate_signal_parameters(frequency: int, sample_rate: int, 
                             switch_interval: int, phase_mask: str) -> Dict:
    """信号生成に必要なパラメータを計算する"""
    bits_count = len(phase_mask)
    samples_per_bit = sample_rate * switch_interval / frequency
    total_samples = int(samples_per_bit * bits_count)
    duration = total_samples / sample_rate
    
    print(f"総ビット数: {bits_count}")
    print(f"1ビットあたりのサンプル数: {samples_per_bit:.2f}")
    print(f"総サンプル数: {total_samples}")
    print(f"音声の長さ: {duration:.2f}秒")
    
    return {
        'samples_per_bit': samples_per_bit,
        'total_samples': total_samples,
        'duration': duration
    }

def create_phase_mask(phase_data: str, samples_per_bit: float, 
                     total_samples: int) -> np.ndarray:
    """位相反転のマスクを生成する"""
    mask = np.ones(total_samples)
    for i, bit in enumerate(phase_data):
        if bit == '1':
            start = int(i * samples_per_bit)
            end = int((i + 1) * samples_per_bit)
            mask[start:end] = -1
    return mask

def generate_base_sine_wave(frequency: int, duration: float, 
                          total_samples: int) -> np.ndarray:
    """基本のサイン波を生成する"""
    t = np.linspace(0, duration, total_samples, endpoint=False)
    return np.sin(2 * np.pi * frequency * t)

def normalize_audio(audio: np.ndarray, to_int16: bool = True) -> np.ndarray:
    """音声データを正規化する"""
    normalized = audio / np.max(np.abs(audio))
    if to_int16:
        return (normalized * 32767).astype(np.int16)
    return normalized

def generate_phase_shifting_sine(frequency: int, sample_rate: int, 
                               switch_interval: int, binary_message: str) -> np.ndarray:
    """位相シフトサイン波を生成する"""
    print("\n=== 位相シフトサイン波の生成を開始します ===\n")
    
    # 位相マスクの生成と信号パラメータの計算
    phase_mask = binary_to_bpsk_phase(binary_message)
    print(f"phase_mask: {phase_mask}\n")
    params = calculate_signal_parameters(frequency, sample_rate, switch_interval, phase_mask)
    
    # 基本波形の生成と位相シフトの適用
    sine_wave = generate_base_sine_wave(frequency, params['duration'], params['total_samples'])
    mask = create_phase_mask(phase_mask, params['samples_per_bit'], params['total_samples'])
    phase_shifting_sine = sine_wave * mask
    
    return normalize_audio(phase_shifting_sine)

def combine_audio_signals(*audio_signals: List[np.ndarray], waves: List[Dict]) -> np.ndarray:
    """複数の音声信号を合成する"""
    print("\n=== 複数の音声データの合成を開始します ===\n")
    
    if not audio_signals:
        print("警告: 合成する音声データがありません。")
        return np.array([])
    
    # 最大長に合わせてパディング
    max_length = max(len(signal) for signal in audio_signals)
    print(f"合成する音声データの数: {len(audio_signals)}")
    print(f"最大の音声データ長: {max_length}")
    
    padded_signals = [np.pad(signal, (0, max_length - len(signal)), 'constant')
                     if len(signal) < max_length else signal 
                     for signal in audio_signals]
    
    # 周波数の比率に応じて振幅を調整
    max_freq = max(waves[i]['frequency'] for i in range(len(audio_signals)))
    scaled_signals = [signal * (waves[i]['frequency'] / max_freq)
                     for i, signal in enumerate(padded_signals)]
    
    # 合成と正規化
    combined_signal = np.sum(scaled_signals, axis=0)
    normalized_signal = normalize_audio(combined_signal)
    
    print(f"合成された音声データの長さ: {len(normalized_signal)}")
    print("音声データの合成が完了しました。")
    
    return normalized_signal

def generate_psk_signal(output_file: str, sample_rate: int, 
                       waves: List[Dict]) -> None:
    """PSK信号を生成してファイルに保存する"""
    print(f"パラメータ設定:")
    for i, param in enumerate(waves, 1):
        print(f"パラメータセット {i}:")
        print(f"  周波数: {param['frequency']}Hz")
        print(f"  位相反転間隔: {param['switch_interval']}周期")
        print(f"  メッセージ: '{param['binary_message']}'")
    print(f"サンプリングレート: {sample_rate}Hz")
    print(f"出力ファイル: {output_file}")

    # 各波形の生成と合成
    audio_signals = [
        generate_phase_shifting_sine(
            param['frequency'], 
            sample_rate, 
            param['switch_interval'], 
            param['binary_message']
        ) for param in waves
    ]
    
    combined_audio = combine_audio_signals(*audio_signals, waves=waves)
    save_wav_file(combined_audio, sample_rate, output_file)
    print(f"複数のメッセージを埋め込んだ位相シフトサイン波を {output_file} に生成しました。")

def generate_psk_signal_in_memory(sample_rate: int, waves: List[Dict]) -> np.ndarray:
    """PSK信号をメモリ上で生成して返す"""
    print(f"パラメータ設定:")
    for i, param in enumerate(waves, 1):
        print(f"パラメータセット {i}:")
        print(f"  周波数: {param['frequency']}Hz")
        print(f"  位相反転間隔: {param['switch_interval']}周期")
        print(f"  メッセージ: '{param['binary_message']}'")
    print(f"サンプリングレート: {sample_rate}Hz")

    # 各波形の生成と合成
    audio_signals = [
        generate_phase_shifting_sine(
            param['frequency'], 
            sample_rate, 
            param['switch_interval'], 
            param['binary_message']
        ) for param in waves
    ]
    
    combined_audio = combine_audio_signals(*audio_signals, waves=waves)
    return combined_audio

if __name__ == "__main__":
    output_file = "wav/output.wav"
    sample_rate = 44100
    # ランダムな10000桁のバイナリメッセージを生成
    import random
    binary_message = ''.join([str(random.randint(0, 1)) for _ in range(40)])
    waves = [
        {"frequency": 20000, "switch_interval": 20, "binary_message": binary_message},
    ]

    generate_psk_signal(output_file, sample_rate, waves)