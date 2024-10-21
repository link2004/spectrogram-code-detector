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



# Cメジャーの音階の定義（C3からC5まで、2オクターブ）
NOTES = [48, 52, 55, 60, 64, 67, 72, 76, 79, 84, 88, 91, 96, 100, 103, 108]
 
# 音の長さ（秒）
NOTE_DURATION = 0.1

def char_to_notes(char):
    C = ord(char)
    A = math.floor((33 - math.sqrt(1089 - 8 * C)) / 2)
    S_A = 16 * A - (A * (A - 1)) // 2
    B = A + (C - S_A)
    print(f"C: {C} -> A: {A}, B: {B}")
    return NOTES[A], NOTES[B]


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
                notes = char_to_notes(char)
                play_and_stop_chord(notes)
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
