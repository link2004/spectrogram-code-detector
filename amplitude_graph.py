import pyaudio
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

class AudioStreamVisualizer:
    """リアルタイムで音声データの振幅をグラフィカルに表示するクラスです。"""

    def __init__(self, chunk=8192, format=pyaudio.paInt16, channels=1, rate=44100):
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
        self.win = pg.GraphicsLayoutWidget(title="リアルタイム音声振幅")
        self.plot = self.win.addPlot(title="リアルタイム音声振幅")
        self.curve = self.plot.plot(pen='w')
        self.plot.setYRange(-32768, 32767)
        self.plot.setXRange(0, self.CHUNK - 1)
        self.win.show()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):
        """ストリームからデータを読み込み、グラフを更新します。"""
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            numpydata = np.frombuffer(data, dtype=np.int16)
            self.curve.setData(numpydata)
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

    def start(self):
        """イベントループを開始します。"""
        if __name__ == '__main__':
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
