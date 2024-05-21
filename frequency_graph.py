import pyaudio
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

class AudioStreamVisualizer:
    """リアルタイムで音声データの振幅と周波数特性をグラフィカルに表示するクラスです。"""

    def __init__(self, chunk=1024, format=pyaudio.paInt16, channels=1, rate=16000):
        self.CHUNK = chunk
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(title="リアルタイム音声分析")
        
        # 周波数特性のプロット設定
        self.plot_frequency = self.win.addPlot(title="リアルタイム周波数特性")
        self.curve_frequency = self.plot_frequency.plot(pen='y')
        self.plot_frequency.setLogMode(x=False, y=True)  # y軸を対数スケールに設定
        self.plot_frequency.setYRange(0, 3)
        self.plot_frequency.setXRange(1000, self.RATE // 2)  # ナイキスト周波数まで表示

        self.win.nextRow()  # 次の行にプロット

        self.win.show()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):
        """ストリームからデータを読み込み、振幅と周波数特性のグラフを更新します。"""
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            numpydata = np.frombuffer(data, dtype=np.int16)

            # 周波数データの計算とプロット
            fft_data = np.fft.rfft(numpydata)
            fft_magnitude = np.abs(fft_data) / self.CHUNK  # 正規化
            frequency = np.linspace(0, self.RATE / 2, len(fft_magnitude))
            self.curve_frequency.setData(frequency, fft_magnitude)

        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

    def start(self):
        """イベントループを開始します。"""
        self.app.exec_()

    def close(self):
        """ストリームとPyAudioをクリーンアップします。"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

# メイン関数
if __name__ == '__main__':
    visualizer = AudioStreamVisualizer()
    try:
        visualizer.start()
    finally:
        visualizer.close()
