from pynput import keyboard
import time
import math
import sounddevice as sd
import numpy as np
import pyaudio
import threading  # threadingモジュールをインポート

# 対応する周波数（Hz）の配列
FREQUENCY = [
    523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50,  # C5, D5, E5, F5, G5, A5, B5, C6
    1174.66, 1318.51, 1396.91, 1567.98, 1760.00, 1975.53, 2093.00, 2349.32  # D6, E6, F6, G6, A6, B6, C7, D7
]

# 音の長さ（秒）
NOTE_DURATION = 0.1

def char_to_index(char):
    C = ord(char)
    A = math.floor((33 - math.sqrt(1089 - 8 * C)) / 2)
    S_A = 16 * A - (A * (A - 1)) // 2
    B = A + (C - S_A)
    print(f"C: {C} -> A: {A}, B: {B}")
    return A, B

def play_and_stop_chord(notes, velocity=100):
    for note in notes:
        if note < len(FREQUENCY):  # 周波数リストの範囲内か確認
            print(f"note: {FREQUENCY[note]}")
            play_chord([FREQUENCY[note]], NOTE_DURATION, 1.0, 44100 )

def play_chord(frequencies, duration, amplitude=1.0, sample_rate=44100):
    """
    複数の周波数を同時に再生して和音を作る関数

    :param frequencies: 周波数のリスト（Hz）
    :param duration: 再生時間（秒）
    :param amplitude: 振幅（0.0から1.0の間）
    :param sample_rate: サンプリングレート（Hz）
    """
    # PyAudioの初期化
    p = pyaudio.PyAudio()

    # ストリームを開く
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True)

    # 時間配列を生成
    t = np.arange(int(sample_rate * duration)) / sample_rate

    # 各周波数のサイン波を生成し、合成
    chord = np.zeros_like(t)
    for freq in frequencies:
        chord += amplitude * np.sin(2 * np.pi * freq * t)

    # 振幅を正規化
    if len(frequencies) > 0:
        chord /= len(frequencies)

    # クリッピングを防ぐためにノーマライズ
    max_amplitude = np.max(np.abs(chord))
    if max_amplitude > 1.0:
        chord = chord / max_amplitude

    # 音を再生
    stream.write(chord.astype(np.float32).tobytes())

    # ストリームを停止して閉じる
    stream.stop_stream()
    stream.close()
    p.terminate()

def on_press(key):
    global instrument_index
    try:
        if key == keyboard.Key.esc:  # ESCキーで終了
            return False
        else:
            char = key.char
            print(char)
            if char:
                A, B = char_to_index(char)
                notes = [FREQUENCY[A],FREQUENCY[B]]
                thread = threading.Thread(target=play_chord, args=(notes, NOTE_DURATION))
                thread.start()  # play_chordを別スレッドで実行
                print(f"{FREQUENCY[A]}, {FREQUENCY[B]}")
    except AttributeError:
        pass

print("キーボードの入力を音に変換します。終了するにはESCキーを押してください。")

# キーボードリスナーの設定と開始
listener = keyboard.Listener(on_press=on_press)
listener.start()

# メインループ
try:
    while listener.is_alive():
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

# クリーンアップ
listener.stop()
