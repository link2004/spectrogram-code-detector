import pyaudio
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
from scipy.signal import find_peaks

class AudioStreamVisualizer:
    """リアルタイムで音声データのスペクトログラムをグラフィカルに表示し、指定された周波数を検出します。"""

    def __init__(self, chunk=2048, format=pyaudio.paInt16, channels=1, rate=16000, history_length=100):
        self.CHUNK = chunk
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate
        self.HISTORY_LENGTH = history_length
        self.NFFT = 4096  # FFTのポイント数を増やして周波数分解能を高める
        self.FREQUENCY = [
            523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50,
            1174.66, 1318.51, 1396.91, 1567.98, 1760.00, 1975.53, 2093.00, 2349.32
        ]
        self.frequency_tolerance = 5  # 許容誤差を5Hzに設定
        self.frequencies = np.fft.rfftfreq(self.NFFT, 1.0 / self.RATE)
        self.init_audio_stream()
        self.setup_gui()
        self.setup_timer()

    def init_audio_stream(self):
        """オーディオストリームを初期化します。"""
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def setup_gui(self):
        """グラフィカルユーザーインターフェースをセットアップ"""
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(title="リアルタイムスペクトログラム")
        self.plot_spectrogram = self.win.addPlot(title="リアルタイムスペクトログラム")
        self.spectrogram = pg.ImageItem()
        self.plot_spectrogram.addItem(self.spectrogram)
        self.spectrogram_data = np.zeros((self.HISTORY_LENGTH, self.NFFT // 2 + 1))
        self.spectrogram.setImage(self.spectrogram_data)
        self.spectrogram.setRect(pg.QtCore.QRectF(0, 0, self.HISTORY_LENGTH, self.RATE / 2))
        self.plot_spectrogram.setLabel('left', 'Frequency (Hz)')
        self.plot_spectrogram.setLabel('bottom', 'Time (Frames)')
        self.plot_spectrogram.setLimits(yMin=0, yMax=self.RATE / 2)
        self.plot_spectrogram.setRange(yRange=[0, self.RATE / 2])
        self.win.show()

    def setup_timer(self):
        """タイマーを設定して定期的にデータを更新"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def compute_fft(self, data):
        """FFTを計算して正規化"""
        numpydata = np.frombuffer(data, dtype=np.int16)
        window = np.hanning(len(numpydata))
        windowed_data = numpydata * window
        padded_data = np.zeros(self.NFFT)
        padded_data[:len(windowed_data)] = windowed_data
        fft_data = np.fft.rfft(padded_data)
        fft_magnitude = np.abs(fft_data) / len(numpydata)
        fft_magnitude = 20 * np.log10(fft_magnitude + 1e-10)
        return fft_magnitude

    def parabolic(self, f, x):
        """ピークの位置をパラボリック補間で精密化"""
        if x <= 0 or x >= len(f) - 1:
            return x, f[x]
        xv = 1/2 * (f[x - 1] - f[x + 1]) / (f[x - 1] - 2 * f[x] + f[x + 1]) + x
        yv = f[x] - 1/4 * (f[x - 1] - f[x + 1]) * (xv - x)
        return (xv, yv)

    def update(self):
        """ストリームからデータを読み込み、スペクトログラムとピークを更新"""
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            fft_data = self.compute_fft(data)
            # ピークを検出
            peaks, _ = find_peaks(fft_data, height=10)
            # エッジのピークを除外
            peaks = peaks[(peaks > 0) & (peaks < len(fft_data) - 1)]
            if len(peaks) > 0:
                true_peaks = []
                for peak in peaks:
                    interpolated_peak, _ = self.parabolic(fft_data, peak)
                    frequency = interpolated_peak * self.RATE / self.NFFT
                    true_peaks.append(frequency)
                # 検出された周波数を指定された周波数にマッピング
                detected_frequencies = []
                for freq in true_peaks:
                    closest_freq = min(self.FREQUENCY, key=lambda x: abs(x - freq))
                    if abs(closest_freq - freq) <= self.frequency_tolerance:
                        detected_frequencies.append(closest_freq)
                detected_frequencies = list(set(detected_frequencies))  # 重複を削除
                if 0 < len(detected_frequencies) <= 2:
                    print(f"検出された周波数: {detected_frequencies} Hz")
            self.update_spectrogram(fft_data)
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

    def update_spectrogram(self, fft_data):
        """スペクトログラムデータを更新"""
        self.spectrogram_data = np.roll(self.spectrogram_data, 1, axis=0)
        self.spectrogram_data[0, :] = fft_data
        self.spectrogram.setImage(self.spectrogram_data, autoLevels=False, levels=(10, 40))

    def start(self):
        """イベントループを開始"""
        self.app.exec_()

    def close(self):
        """ストリームとPyAudioをクリーンアップ"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == '__main__':
    visualizer = AudioStreamVisualizer()
    try:
        visualizer.start()
    finally:
        visualizer.close()
