import pygame.midi
from pynput import keyboard
import time
import threading
import math

# Pygameの初期化
pygame.init()
pygame.midi.init()

# MIDIプレイヤーの設定
player = pygame.midi.Output(pygame.midi.get_default_output_id())
instruments = [0,13,79,109,115,118,120,124]
instrument_index = 0
player.set_instrument(instruments[instrument_index], 0)  # チャンネル0にグランドピアノ（音色0）を設定



# Cメジャースケールの音階定義（C5からD7まで）
# 各数字はMIDIノート番号と周波数(Hz)を表しています
NOTES = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84, 86]

# 対応する周波数（Hz）の配列
FREQUENCY = [
    523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50,  # C5, D5, E5, F5, G5, A5, B5, C6
    1174.66, 1318.51, 1396.91, 1567.98, 1760.00, 1975.53, 2093.00, 2349.32  # D6, E6, F6, G6, A6, B6, C7, D7
]

# このスケールはCメジャーコードの構成音（C, D, E, F, G, A, B）を2オクターブにわたって並べています
# 隣接する音の周波数比は約1.12（全音）または約1.06（半音）です

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
        player.note_on(note, velocity, 0)
    
    # 指定した時間後に音を止める
    def stop_notes():
        time.sleep(NOTE_DURATION)
        for note in notes:
            player.note_off(note, velocity, 0)
    
    # 別スレッドで音を止める処理を実行
    threading.Thread(target=stop_notes).start()

def on_press(key):
    global instrument_index
    try:
        if key == keyboard.Key.space:
            instrument_index = (instrument_index + 1) % len(instruments)
            player.set_instrument(instruments[instrument_index], 0)
            print(f"楽器を{instruments[instrument_index]}に変更しました")
        elif key == keyboard.Key.esc:  # ESCキーで終了
            return False
        else:
            char = key.char
            print(char)
            if char:
                A, B = char_to_index(char)
                notes = [NOTES[A], NOTES[B]]
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
