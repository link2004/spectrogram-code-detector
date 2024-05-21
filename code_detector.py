import pyaudio
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

class AudioStreamVisualizer:
    """リアルタイムで音声データのスペクトログラムをグラフィカルに表示するクラスです。"""

    def __init__(self, chunk=1024, format=pyaudio.paInt16, channels=1, rate=16000, history_length=100):
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

            # 1000Hz以下の周波数成分をカット
            fft_data = self.high_path_filter(fft_data, 1000)

            # fft_dataの20値以下(小さな音)をカット
            fft_data = np.where(fft_data < 35, 0, fft_data)

            self.update_spectrogram(fft_data)

            frequency = self.detect_pitch(fft_data)
            # print(f"Frequency: {frequency:.2f} Hz")

            code = self.detect_code_from_pitch(frequency)
            # print(code, end='', flush=True)
            variance = self.compute_variance(fft_data)
            if np.abs(variance) < 6:
                print(code, end='', flush=True)
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

    def compute_fft(self, data):
        """FFTを計算して正規化"""
        numpydata = np.frombuffer(data, dtype=np.int16)
        fft_data = np.fft.rfft(numpydata)
        fft_magnitude = np.abs(fft_data) / self.CHUNK
        fft_magnitude = 20 * np.log10(fft_magnitude + 1e-10)
        return fft_magnitude
    
    # 分散を計算
    def compute_variance(self, fft_data):
        # 周波数の配列 [0,]
        frequencies = np.arange(0, self.RATE//2+1, self.RATE/self.CHUNK)
        # 最大周波数を計算
        pitch = self.detect_pitch(fft_data)
        # 分散を計算
        variance = np.sum((frequencies - pitch)**2 * fft_data)
        if variance == 0:
            return 0
        return np.log10(variance)
        
    
    # 平均周波数を計算
    def compute_mean(self, fft_data):
        # 周波数の配列 [0,]
        frequencies = np.arange(0, self.RATE//2+1, self.RATE/self.CHUNK)

        # fft_dataのマイナス値を0に変換
        fft_data = np.where(fft_data < 0, 0, fft_data)
        
        # 加重平均周波数を計算
        weighted_sum = np.sum(fft_data * frequencies)
        total_amplitude = np.sum(fft_data)

        # 平均周波数
        mean_frequency = weighted_sum / total_amplitude

        return mean_frequency

    def detect_pitch(self, fft_data):
        """FFTデータからピッチを検出"""
        index = np.argmax(fft_data)
        if fft_data[index] < 40:
            return 0
        frequency = index * self.RATE / self.CHUNK
        return frequency
    
    def detect_code_from_pitch(self,frequency):
        """周波数から文字を検出します（周波数の範囲は2000Hzから4000Hz未満とします）。"""
        MIN = 4000
        MAX = 8000
        CODE = 'abcdefghijklmnopqrstuvwxyz1234567890'
        if MIN <= frequency < MAX:
            index = (frequency - MIN) // ((MAX-MIN)/len(CODE)) # インデックスを計算
            return CODE[int(index)]  # 対応する文字を返す
        return ''  # 範囲外の場合は空文字を返す
    
    
    def high_path_filter(self, fft_data, frequency):
        """ハイパスフィルタを適用"""
        index = int(frequency * self.CHUNK / self.RATE)
        fft_data[:index] = 0
        return fft_data
    
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
