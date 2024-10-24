import pygame.midi
from pynput import keyboard
import time
import threading
import math
import sounddevice as sd
import numpy as np

# Pygameの初期化
pygame.init()
pygame.midi.init()

# MIDIプレイヤーの設定
player = pygame.midi.Output(pygame.midi.get_default_output_id())
instruments = [0,13,79,109,115,118,120,124]
instrument_index = 0
player.set_instrument(instruments[instrument_index], 0)  # チャンネル0にグランドピアノ（音色0）を設定



# Cメジャースケールの音階定義（C3からC8まで、5オクターブ）
# 各数字はMIDIノート番号と周波数(Hz)を表しています
NOTES = [48, 52, 55, 60, 64, 67, 72, 76, 79, 84, 88, 91, 96, 100, 103, 108]

# 対応する周波数（Hz）の配列
FREQUENCY = [
    130.81, 164.81, 196.00,  # C3, E3, G3
    261.63, 329.63, 392.00,  # C4, E4, G4
    523.25, 659.25, 783.99,  # C5, E5, G5
    1046.50, 1318.51, 1567.98,  # C6, E6, G6
    2093.00, 2637.02, 3135.96,  # C7, E7, G7
    4186.01  # C8
]

# このスケールはCメジャーコードの構成音（C, E, G）を5オクターブにわたって並べています
# 隣接する音の周波数比は約1.26（4分の5音）または約1.19（長3度）です

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
        play_chord([FREQUENCY[note]], NOTE_DURATION, 1.0, 16000)

def play_chord(frequencies, duration, amplitude=1.0, sample_rate=16000):
    """
    複数の周波数を同時に再生して和音を作る関数

    :param frequencies: 周波数のリスト（Hz）
    :param duration: 再生時間（秒）
    :param amplitude: 振幅（0.0から1.0の間）
    :param sample_rate: サンプリングレート（Hz）
    """
    # 時間配列を生成
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 各周波数のサイン波を生成し、合成
    chord = np.zeros_like(t)
    for freq in frequencies:
        chord += amplitude * np.sin(2 * np.pi * freq * t)

    # 振幅を正規化
    chord /= len(frequencies)

    # クリッピングを防ぐためにノーマライズ
    max_amplitude = np.max(np.abs(chord))
    if max_amplitude > 1.0:
        chord = chord / max_amplitude

    # 音を再生
    sd.play(chord, sample_rate)
    sd.wait()

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
                notes = [A,B]
                play_and_stop_chord(notes)
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
player.close()
pygame.midi.quit()
pygame.quit()
