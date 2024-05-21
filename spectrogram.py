import pyaudio
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

class AudioStreamVisualizer:
    """リアルタイムで音声データのスペクトログラムをグラフィカルに表示するクラスです。"""

    def __init__(self, chunk=2048, format=pyaudio.paInt16, channels=1, rate=16000, history_length=100):
        self.CHUNK = chunk
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate
        self.HISTORY_LENGTH = history_length
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
        self.spectrogram_data = np.zeros((self.HISTORY_LENGTH, self.CHUNK // 2 + 1))
        self.spectrogram.setImage(self.spectrogram_data)
        self.spectrogram.setRect(pg.QtCore.QRectF(0, 0, self.HISTORY_LENGTH, self.RATE / 2))
        self.plot_spectrogram.setLabel('left', 'Frequency (Hz)')
        self.plot_spectrogram.setLabel('bottom', 'Time (Samples)')

        self.win.show()

    def setup_timer(self):
        """タイマーを設定して定期的にデータを更新"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):
        """ストリームからデータを読み込み、スペクトログラムを更新"""
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            fft_data = self.compute_fft(data)
            self.update_spectrogram(fft_data)
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

    def compute_fft(self, data):
        """FFTを計算して正規化"""
        numpydata = np.frombuffer(data, dtype=np.int16)
        fft_data = np.fft.rfft(numpydata)
        fft_magnitude = np.abs(fft_data) / self.CHUNK
        fft_magnitude = 20 * np.log10(fft_magnitude + 1e-10)
        return fft_magnitude

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

if __name__ == '__main__':
    visualizer = AudioStreamVisualizer()
    try:
        visualizer.start()
    finally:
        visualizer.close()
