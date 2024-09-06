import numpy as np
import pyaudio
from scipy.fftpack import fft
import tkinter as tk
from tkinter import ttk
import threading

class PSKDetector:
    def __init__(self, frequency=2000, interval_cycles=4, sample_rate=44100, chunk_size=4410, phase_threshold=0.8, amplitude_threshold=0.1):
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.phase_threshold = phase_threshold
        self.amplitude_threshold = amplitude_threshold
        self.interval_cycles = interval_cycles
        
        self.samples_per_cycle = int(sample_rate / frequency)
        self.interval_samples = self.samples_per_cycle * interval_cycles
        
        # chunk_size を interval_samples の倍数に調整
        self.chunk_size = self.interval_samples * max(1, chunk_size // self.interval_samples)
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=sample_rate,
                                  input=True,
                                  frames_per_buffer=self.chunk_size)
        self.reference = np.sin(2 * np.pi * frequency * np.arange(self.chunk_size) / sample_rate)
        
        self.current_amplitude = 0
        self.detection_result = ""
        self.previous_phase = None
        self.hyst_high = phase_threshold * np.pi
        self.hyst_low = 0.7 * self.hyst_high  # ヒステリシス低閾値

    def detect_phase_shift(self, signal):
        # signal の長さが interval_samples の倍数になるように調整
        num_intervals = len(signal) // self.interval_samples
        signal = signal[:num_intervals * self.interval_samples]
        signal_chunks = signal.reshape(-1, self.interval_samples)
        
        results = []
        for chunk in signal_chunks:
            fft_result = fft(chunk)
            freqs = np.fft.fftfreq(len(chunk), 1/self.sample_rate)
            target_index = np.argmin(np.abs(freqs - self.frequency))
            
            amplitude = np.abs(fft_result[target_index]) / len(chunk)
            self.current_amplitude = amplitude
            
            if amplitude > self.amplitude_threshold:
                phase = np.angle(fft_result[target_index])
                
                if self.previous_phase is not None:
                    phase_diff = np.angle(np.exp(1j * (phase - self.previous_phase)))
                    
                    if abs(phase_diff) > self.hyst_high:
                        results.append(1)
                    elif abs(phase_diff) < self.hyst_low:
                        results.append(0)
                    else:
                        results.append(results[-1] if results else 0)
                else:
                    results.append(0)
                
                self.previous_phase = phase
            else:
                results.append(0)
        
        return results

    def run(self):
        try:
            while True:
                data = np.frombuffer(self.stream.read(self.chunk_size), dtype=np.float32)
                # 移動平均フィルタの適用
                window_size = 5
                data_smooth = np.convolve(data, np.ones(window_size)/window_size, mode='valid')
                results = self.detect_phase_shift(data_smooth)
                self.detection_result = ''.join(map(str, results))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

class Application(tk.Tk):
    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.title("PSK Detector")
        self.geometry("400x300")
        
        self.amplitude_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.amplitude_bar.pack(pady=20)
        
        self.amplitude_label = tk.Label(self, text="Amplitude: 0.0")
        self.amplitude_label.pack()
        
        self.result_text = tk.Text(self, height=10, width=50)
        self.result_text.pack(pady=20)
        
        self.update_ui()

    def update_ui(self):
        amplitude = self.detector.current_amplitude
        self.amplitude_bar["value"] = min(amplitude * 100, 100)  # 0-100の範囲に正規化
        self.amplitude_label.config(text=f"Amplitude: {amplitude:.4f}")
        
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, self.detector.detection_result)
        
        self.after(100, self.update_ui)  # 100ミリ秒ごとに更新

if __name__ == "__main__":
    detector = PSKDetector(frequency=440, interval_cycles=8, amplitude_threshold=0.001)
    
    app = Application(detector)
    
    detector_thread = threading.Thread(target=detector.run)
    detector_thread.daemon = True
    detector_thread.start()
    
    app.mainloop()