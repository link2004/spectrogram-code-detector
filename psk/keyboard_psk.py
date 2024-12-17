import keyboard
import time
import numpy as np
from pskgenerator import generate_psk_signal, generate_psk_signal_in_memory
import sounddevice as sd
import wave

# グローバル変数として設定
SAMPLE_RATE = 44100
# sounddeviceの初期化
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
sd.default.dtype = np.int16

def split_16bit_to_4bits(binary_16bit: str) -> list:
    """16ビットの文字列を4ビットずつに分割"""
    return [binary_16bit[i:i+4] for i in range(0, 16, 4)]

def calculate_parity(binary_str: str) -> str:
    """8ビットのパリティビットを計算"""
    count_ones = sum(1 for bit in binary_str if bit == '1')
    return binary_str + ('0' if count_ones % 2 == 0 else '1')

def play_audio_data(audio_data: np.ndarray, sample_rate: int):
    """メモリ上の音声データを再生"""
    try:
        # 前の再生が終わっていない場合は停止
        sd.stop()
        
        # データ型の確認と変換
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # 音声データを再生
        sd.play(audio_data, sample_rate, blocking=False)
        
    except Exception as e:
        print(f"音声再生エラー: {e}")
        print(f"音声データ情報: shape={audio_data.shape}, dtype={audio_data.dtype}")
        print(f"サンプルレート: {sample_rate}")

def on_key_press(event):
    # 入力された文字を取得
    character = event.name
    
    # 特殊キーの処理
    if character in ['backspace', 'delete', 'space']:
        if character == 'backspace':
            char_code = 8
        elif character == 'delete':
            char_code = 127
        else:  # space
            char_code = 32
    else:
        # 通常の文字の処理
        if len(character) == 1:
            char_code = ord(character)
        else:
            return

    try:
        # 7ビットの2進数に変換
        binary_7bit = bin(char_code)[2:].zfill(7)
        # パリティビットを追加して8ビットにする
        binary_8bit = calculate_parity(binary_7bit)
        # 16ビットにする（同じ8ビットを2回繰り返す）
        binary_16bit = binary_8bit * 2
        
        # 4ビットずつに分割
        four_bits = split_16bit_to_4bits(binary_16bit)
        
        # 波形パラメータを設定
        waves = [
            {"frequency": 4410, "switch_interval": 55, "binary_message": four_bits[0]},
            {"frequency": 3308, "switch_interval": 41, "binary_message": four_bits[1]},
            {"frequency": 2756, "switch_interval": 34, "binary_message": four_bits[2]},
            {"frequency": 2205, "switch_interval": 28, "binary_message": four_bits[3]},
        ]
        
        # 生成した音声データを直接再生
        audio_data = generate_psk_signal_in_memory(SAMPLE_RATE, waves)
        play_audio_data(audio_data, SAMPLE_RATE)
        
        # デバッグ情報を表示
        print(f"文字: '{character}'")
        print(f"文字コード: {char_code}")
        print(f"7bit: {binary_7bit}")
        print(f"8bit with parity: {binary_8bit}")
        print(f"16bit: {binary_16bit}")
        print(f"4bit splits: {four_bits}")
        print("-" * 40)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# メイン処理
if __name__ == "__main__":
    try:
        print("キーボードの入力を監視中... (終了するには 'esc' キーを押してください)")
        
        # キー入力のイベントハンドラを設定
        keyboard.on_press(on_key_press)
        
        # escキーが押されるまで実行を継続
        keyboard.wait('esc')
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        print("プログラムを終了します。")
        sd.stop()  # 終了時に再生を停止 