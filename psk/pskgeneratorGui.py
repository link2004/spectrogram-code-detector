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

        pygame.mixer.init()

        self.frequency_var = tk.IntVar(value=1000)
        self.bps_var = tk.StringVar(value="1000")

        self.create_widgets()

    def create_widgets(self):
        # 周波数関連のウィジェット
        self.create_frequency_widgets()

        # bps関連のウィジェット
        self.create_bps_widgets()

        # ファイルの長さ指定用のウィジェット
        self.create_duration_widget()

        # バイナリメッセージ入力
        self.create_binary_message_widgets()

        # 波形関連のウィジェット
        self.create_wave_widgets()

        # 生成と再生ボタン
        self.play_button = ttk.Button(self.master, text="生成して再生", command=self.generate_and_play)
        self.play_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

    def create_frequency_widgets(self):
        ttk.Label(self.master, text="周波数 (Hz):").grid(row=0, column=0, padx=5, pady=5)
        self.frequency_slider = ttk.Scale(self.master, from_=100, to=2000, variable=self.frequency_var, orient=tk.HORIZONTAL, length=200, command=self.update_frequency)
        self.frequency_slider.grid(row=0, column=1, padx=5, pady=5)
        self.frequency_entry = ttk.Entry(self.master, textvariable=self.frequency_var, width=5)
        self.frequency_entry.grid(row=0, column=2, padx=5, pady=5)
        self.frequency_entry.bind('<Return>', self.update_frequency_from_entry)

    def create_bps_widgets(self):
        ttk.Label(self.master, text="データレート (bps):").grid(row=1, column=0, padx=5, pady=5)
        self.bps_dropdown = ttk.Combobox(self.master, textvariable=self.bps_var, state="readonly", width=10)
        self.bps_dropdown.grid(row=1, column=1, padx=5, pady=5)
        self.bps_dropdown.bind("<<ComboboxSelected>>", self.update_bps)

    def create_duration_widget(self):
        ttk.Label(self.master, text="ファイルの長さ (秒):").grid(row=3, column=0, padx=5, pady=5)
        self.duration_entry = ttk.Entry(self.master, textvariable=self.duration_var, width=5)
        self.duration_entry.grid(row=3, column=1, padx=5, pady=5)

    def create_binary_message_widgets(self):
        ttk.Label(self.master, text="バイナリメッセージ:").grid(row=2, column=0, padx=5, pady=5)
        self.binary_message_entry = ttk.Entry(self.master)
        self.binary_message_entry.grid(row=2, column=1, columnspan=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.master, text="自動生成", command=self.generate_random_binary).grid(row=2, column=2, padx=5, pady=5)

    def create_wave_widgets(self):
        ttk.Button(self.master, text="波形を追加", command=self.add_wave).grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.wave_listbox = tk.Listbox(self.master, width=50, height=10)
        self.wave_listbox.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=self.wave_listbox.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.wave_listbox.configure(yscrollcommand=scrollbar.set)
        ttk.Button(self.master, text="選択した波形を削除", command=self.remove_selected_wave).grid(row=6, column=0, columnspan=2, padx=5, pady=5)

    def generate_random_binary(self):
        frequency = self.frequency_var.get()
        bps = int(self.bps_var.get())  # 文字列から整数に変換
        duration = self.duration_var.get()
        
        max_bits = int(bps * duration)
        random_binary = ''.join(random.choice('01') for _ in range(max_bits))
        return random_binary

    def add_wave(self):
        try:
            frequency = self.frequency_var.get()
            bps = int(self.bps_var.get())  # 文字列から整数に変換
            switch_interval = self.calculate_switch_interval(frequency, bps)
            binary_message = self.generate_random_binary()

            actual_bps = round(frequency / switch_interval)  # 実際のbpsを計算

            wave = {
                "frequency": frequency,
                "bps": actual_bps,
                "switch_interval": switch_interval,
                "binary_message": binary_message
            }
            self.waves.append(wave)
            self.wave_listbox.insert(tk.END, f"{frequency}Hz, {actual_bps}bps ({switch_interval}周期), {binary_message}")

        except ValueError as e:
            messagebox.showerror("エラー", str(e))

    def calculate_switch_interval(self, frequency, bps):
        return max(1, round(frequency / bps))  # 最小値を1に設定し、四捨五入して整数に

    def generate_and_play(self):
        if not self.waves:
            self.add_wave()  # 波形がない場合は自動的に追加

        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.play_button.config(text="生成して再生")
        else:
            self.generate_wav()
            if self.output_file:
                self.play_audio()

    def generate_wav(self):
        if not self.waves:
            print("エラー: 波形が追加されていません。")
            return

        current_date = datetime.datetime.now().strftime("%Y%m%d")
        default_save_directory = os.path.join(".", "wav", current_date)
        os.makedirs(default_save_directory, exist_ok=True)

        # 時間を削除し、ファイル名を簡略化
        filename = f"PSK_{self.waves[0]['frequency']}Hz_{self.waves[0]['switch_interval']}cycle.wav"
        counter = 1
        original_filename = filename
        while os.path.exists(os.path.join(default_save_directory, filename)):
            filename = f"{os.path.splitext(original_filename)[0]}_{counter}{os.path.splitext(original_filename)[1]}"
            counter += 1

        self.output_file = os.path.join(default_save_directory, filename)

        audio_signals = []
        for wave in self.waves:
            audio = generate_phase_shifting_sine(wave['frequency'], self.sample_rate, wave['switch_interval'], wave['binary_message'])
            audio_signals.append(audio)

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

    def update_frequency(self, event=None):
        frequency = int(float(self.frequency_slider.get()))
        self.frequency_var.set(frequency)
        self.update_bps_options()

    def update_frequency_from_entry(self, event=None):
        try:
            value = int(self.frequency_entry.get())
            if 100 <= value <= 2000:
                self.frequency_var.set(value)
                self.frequency_slider.set(value)
                self.update_bps_options()
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "周波数は100から2000の整数である必要があります。")
            self.frequency_entry.delete(0, tk.END)
            self.frequency_entry.insert(0, str(self.frequency_var.get()))

    def update_bps_options(self):
        frequency = self.frequency_var.get()
        options = []
        prev_bps = None
        for n in range(1, frequency + 1):
            bps = round(frequency / n)
            if bps != prev_bps:
                options.append(str(bps))
                prev_bps = bps
        self.bps_dropdown['values'] = options
        if self.bps_var.get() not in options:
            self.bps_var.set(options[0])

    def update_bps(self, event=None):
        # bpsの更新処理（必要に応じて）
        pass

    def remove_selected_wave(self):
        selected_indices = self.wave_listbox.curselection()
        if not selected_indices:
            print("警告: 削除する波形を選択してください。")
            return

        for index in reversed(selected_indices):
            del self.waves[index]
            self.wave_listbox.delete(index)

        print("選択した波形が削除されました。")

if __name__ == "__main__":
    root = tk.Tk()
    gui = PSKGeneratorGUI(root)
    root.mainloop()