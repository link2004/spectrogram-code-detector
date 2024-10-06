import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import pygame
import threading
import random
from pskgenerator import generate_phase_shifting_sine, combine_audio_signals, output_wav_file
import datetime
import os
import math

class PSKGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("PSK ジェネレーター GUI")
        master.geometry("600x400")

        self.waves = []
        self.output_file = None
        self.sample_rate = 16000
        self.is_playing = False
        self.duration_var = tk.DoubleVar(value=5.0)
        self.num_frequencies = tk.IntVar(value=1)
        self.frequencies = []
        self.bps_values = []

        pygame.mixer.init()

        self.create_widgets()

    def create_widgets(self):
        # 周波数の数を指定するウィジェット
        self.create_num_frequencies_widget()

        # 周波数とbpsの設定用ウィジェット
        self.create_frequency_bps_widgets()

        # ファイルの長さ指定用のウィジェット
        self.create_duration_widget()

        # バイナリメッセージ入力
        self.create_binary_message_widgets()

        # 生成と再生ボタン
        self.play_button = ttk.Button(self.master, text="生成して再生", command=self.generate_and_play)
        self.play_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

    def create_num_frequencies_widget(self):
        ttk.Label(self.master, text="周波数の数:").grid(row=0, column=0, padx=5, pady=5)
        num_freq_spinbox = ttk.Spinbox(self.master, from_=1, to=10, textvariable=self.num_frequencies, command=self.update_frequency_bps_widgets, width=5)
        num_freq_spinbox.grid(row=0, column=1, padx=5, pady=5)

    def create_frequency_bps_widgets(self):
        self.freq_bps_frame = ttk.Frame(self.master)
        self.freq_bps_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.update_frequency_bps_widgets()

    def update_frequency_bps_widgets(self):
        num_freq = self.num_frequencies.get()
        current_freq = len(self.frequencies)

        # 新しい周波数とBPS値を追加
        if num_freq > current_freq:
            for _ in range(num_freq - current_freq):
                self.frequencies.append(tk.IntVar(value=200))
                self.bps_values.append(tk.StringVar(value="200"))
        # 余分な周波数とBPS値を削除
        elif num_freq < current_freq:
            self.frequencies = self.frequencies[:num_freq]
            self.bps_values = self.bps_values[:num_freq]

        # ウィジェットを更新
        for widget in self.freq_bps_frame.winfo_children():
            widget.destroy()

        for i in range(num_freq):
            ttk.Label(self.freq_bps_frame, text=f"周波数 {i+1} (Hz):").grid(row=i, column=0, padx=5, pady=2)
            freq_entry = ttk.Entry(self.freq_bps_frame, textvariable=self.frequencies[i], width=10)
            freq_entry.grid(row=i, column=1, padx=5, pady=2)
            freq_entry.bind('<FocusOut>', lambda e, idx=i: self.update_bps_options(idx))

            ttk.Label(self.freq_bps_frame, text=f"BPS {i+1}:").grid(row=i, column=2, padx=5, pady=2)
            bps_dropdown = ttk.Combobox(self.freq_bps_frame, textvariable=self.bps_values[i], state="readonly", width=10)
            bps_dropdown.grid(row=i, column=3, padx=5, pady=2)
            self.update_bps_options(i)

    def create_duration_widget(self):
        ttk.Label(self.master, text="ファイルの長さ (秒):").grid(row=3, column=0, padx=5, pady=5)
        self.duration_var.set(1)  # 初期値を1に設定
        self.duration_entry = ttk.Entry(self.master, textvariable=self.duration_var, width=5)
        self.duration_entry.grid(row=3, column=1, padx=5, pady=5)

    def create_binary_message_widgets(self):
        ttk.Label(self.master, text="バイナリメッセージ:").grid(row=2, column=0, padx=5, pady=5)
        self.binary_message_entry = ttk.Entry(self.master)
        self.binary_message_entry.grid(row=2, column=1, columnspan=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.master, text="自動生成", command=self.generate_random_binary).grid(row=2, column=2, padx=5, pady=5)

    def generate_random_binary(self):
        frequency = self.frequencies[0].get()
        bps = int(self.bps_values[0].get())  # 文字列から整数に変換
        duration = self.duration_var.get()
        
        max_bits = int(bps * duration)
        random_binary = ''.join(random.choice('01') for _ in range(max_bits))
        return random_binary

    def calculate_switch_interval(self, frequency, bps):
        return max(1, round(frequency / bps))  # 最小値を1に設定し、四捨五入して整数に

    def generate_and_play(self):
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.play_button.config(text="生成して再生")
        else:
            self.generate_wav()
            if self.output_file:
                self.play_audio()

    def generate_wav(self):
        audio_signals = []
        filename_parts = []
        for freq_var, bps_var in zip(self.frequencies, self.bps_values):
            frequency = freq_var.get()
            bps = int(bps_var.get())
            switch_interval = self.calculate_switch_interval(frequency, bps)
            binary_message = self.generate_random_binary()
            audio = generate_phase_shifting_sine(frequency, self.sample_rate, switch_interval, binary_message)
            audio_signals.append(audio)
            filename_parts.append(f"{frequency}Hz_{switch_interval}cycle")

        current_date = datetime.datetime.now().strftime("%Y%m%d")
        default_save_directory = os.path.join(".", "wav", current_date)
        os.makedirs(default_save_directory, exist_ok=True)

        # すべてのパラメーターを含むファイル名を生成
        filename = f"PSK_{'_'.join(filename_parts)}.wav"
        counter = 1
        original_filename = filename
        while os.path.exists(os.path.join(default_save_directory, filename)):
            filename = f"{os.path.splitext(original_filename)[0]}_{counter}{os.path.splitext(original_filename)[1]}"
            counter += 1

        self.output_file = os.path.join(default_save_directory, filename)

        combined_audio = combine_audio_signals(*audio_signals)
        try:
            output_wav_file(combined_audio, self.sample_rate, self.output_file)
            print(f"WAVファイルが生成されました: {self.output_file}")
        except PermissionError:
            messagebox.showerror("エラー", f"ファイル {self.output_file} への書き込み権限がありません。")
        except Exception as e:
            messagebox.showerror("エラー", f"WAVファイルの生成中にエラーが発生しました: {str(e)}")

    def play_audio(self):
        def play_thread():
            pygame.mixer.music.load(self.output_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            self.is_playing = False
            self.master.after(0, lambda: self.play_button.config(text="生成して再生"))

        threading.Thread(target=play_thread, daemon=True).start()
        self.is_playing = True
        self.play_button.config(text="停止")

    def update_bps_options(self, index):
        frequency = self.frequencies[index].get()
        options = []
        prev_bps = None
        for n in range(1, frequency + 1):
            bps = round(frequency / n)
            if bps != prev_bps:
                options.append(str(bps))
                prev_bps = bps
        dropdown = self.freq_bps_frame.winfo_children()[index * 4 + 3]
        dropdown['values'] = options
        if self.bps_values[index].get() not in options:
            self.bps_values[index].set(options[0])

if __name__ == "__main__":
    root = tk.Tk()
    gui = PSKGeneratorGUI(root)
    root.mainloop()