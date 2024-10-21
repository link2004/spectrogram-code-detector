import pygame.midi
import pygame
from pynput import keyboard
import time
import threading
import math
import numpy as np

# Pygameの初期化
pygame.init()
pygame.midi.init()
pygame.mixer.init(size=32)

# MIDIプレイヤーの設定
player = pygame.midi.Output(pygame.midi.get_default_output_id())
instruments = [0,13,79,109,115,118,120,124]
instrument_index = 0
player.set_instrument(instruments[instrument_index], 0)

# 音階の定義（C3からB4まで）
NOTES = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74]

# 音の長さ（秒）
NOTE_DURATION = 0.1

# 音色モード（True: 楽器音、False: sin波）
use_instrument = True

def char_to_notes(char):
    C = ord(char)
    A = math.floor((33 - math.sqrt(1089 - 8 * C)) / 2)
    S_A = 16 * A - (A * (A - 1)) // 2
    B = A + (C - S_A)
    print(f"C: {C} -> A: {A}, B: {B}")
    return NOTES[A], NOTES[B]

def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.3):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)
    # エンベロープを適用して音の立ち上がりと減衰を滑らかにする
    envelope = np.linspace(0, 1, len(t))
    envelope = np.minimum(envelope, np.flip(envelope))
    sine_wave *= envelope
    return sine_wave.astype(np.float32)

def play_sine_wave(frequency):
    sine_wave = generate_sine_wave(frequency, NOTE_DURATION)
    # クリッピングを防ぐためにノーマライズ
    max_amplitude = np.max(np.abs(sine_wave))
    if max_amplitude > 1.0:
        sine_wave = sine_wave / max_amplitude
    sound = pygame.mixer.Sound(sine_wave)
    sound.set_volume(0.5)  # 音量を半分に設定
    sound.play()

def play_and_stop_chord(notes, velocity=100):
    if use_instrument:
        for note in notes:
            player.note_on(note, velocity, 0)
        
        def stop_notes():
            time.sleep(NOTE_DURATION)
            for note in notes:
                player.note_off(note, velocity, 0)
        
        threading.Thread(target=stop_notes).start()
    else:
        for note in notes:
            frequency = 440 * (2 ** ((note - 69) / 12))  # MIDI音階から周波数への変換
            play_sine_wave(440)

def on_press(key):
    global instrument_index, use_instrument
    try:
        if key == keyboard.Key.space:
            instrument_index = (instrument_index + 1) % len(instruments)
            player.set_instrument(instruments[instrument_index], 0)
            print(f"楽器を{instruments[instrument_index]}に変更しました")
        elif key == keyboard.Key.tab:
            use_instrument = not use_instrument
            print(f"音色モードを{'楽器音' if use_instrument else 'sin波'}に変更しました")
        elif key == keyboard.Key.esc:
            return False
        else:
            char = key.char
            print(char)
            if char:
                notes = char_to_notes(char)
                play_and_stop_chord(notes)
    except AttributeError:
        pass

print("キーボードの入力を音に変換します。")
print("Spaceキー: 楽器音の変更")
print("Tabキー: 楽器音とsin波の切り替え")
print("ESCキー: 終了")

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
