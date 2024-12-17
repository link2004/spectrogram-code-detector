import sounddevice as sd
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from scipy import signal

# オーディオデバイスの設定
def setup_audio_device():
    """オーディオデバイスの初期設定を行う"""
    device_list = sd.query_devices()
    print("利用可能なオーディオデバイス:")
    print(device_list)
    sd.default.device = [1, 6]  # 入力デバイス:1, 出力デバイス:6

# グローバル変数の設定
GAIN = 1000
FREQUENCY = 8820  # 周波数
SWITCH_INTERVAL = 110 # スイッチ間隔
BANDWIDTH = 500  # バンド幅
SAMPLE_RATE = 44100   # サンプリングレート
BUFFER_SIZE = int(0.5 * SAMPLE_RATE )  # バッファサイズ
DELAY_SAMPLES = SAMPLE_RATE // FREQUENCY * SWITCH_INTERVAL  # ディレイのサンプル数

plotdata_original = np.zeros((BUFFER_SIZE))
plotdata_delay = np.zeros((DELAY_SAMPLES + BUFFER_SIZE))
plotdata_multiply = np.zeros((BUFFER_SIZE))  # 掛け算用の新しい配列を追加

# バンドパスフィルタの設定を追加
def create_bandpass_filter(center_freq, bandwidth):
    """中心周波数とバンド幅でバンドパスフィルタを作成する"""
    nyquist = SAMPLE_RATE * 0.5
    low = (center_freq - bandwidth / 2) / nyquist
    high = (center_freq + bandwidth / 2) / nyquist
    b, a = signal.butter(6, [low, high], btype='band')
    return b, a

def audio_callback(indata, frames, time, status):
    """
    オーディオ入力コールバック関数
    indata: 入力オーディオデータ (shape=(サンプル数, チャンネル数))
    """
    global plotdata_original, plotdata_delay, plotdata_multiply  # グローバル変数に追加
    data = indata[:, 0]
    
    # バンドパスフィルタを適用
    b, a = create_bandpass_filter(FREQUENCY, BANDWIDTH)
    filtered_data = signal.filtfilt(b, a, data) * GAIN

    # 振幅の変化を滑らかに
    filtered_data = signal.medfilt(filtered_data, kernel_size=5)
    
    shift = len(data)
    
    plotdata_original = np.roll(plotdata_original, -shift)
    plotdata_original[-shift:] = filtered_data  # フィルタ適用後のデータを使用
    
    plotdata_delay = np.roll(plotdata_delay, -shift)
    plotdata_delay[-shift:] = filtered_data     # フィルタ適用後のデータを使用
    
    plotdata_multiply = np.roll(plotdata_multiply, -shift)
    plotdata_multiply[-shift:] = filtered_data * plotdata_delay[BUFFER_SIZE-shift:BUFFER_SIZE] * 1000

def update_plot(frame):
    """
    プロット更新用コールバック関数
    matplotlibのアニメーション機能で呼び出される
    """
    global plotdata_original
    lines[0].set_ydata(plotdata_original)
    lines[1].set_ydata(plotdata_delay)
    lines[2].set_ydata(plotdata_multiply)  # 掛け算波形の更新を追加
    return lines

# プロット初期設定
def setup_plot():
    """プロットの初期設定を行う"""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9))  # 3つのサブプロットに変更
    lines = []
    
    # 1つ目の波形のプロット設定
    line1, = ax1.plot(plotdata_original)
    ax1.set_ylim([-1.0, 1.0])
    ax1.set_xlim([0, BUFFER_SIZE])
    ax1.yaxis.grid(True)
    ax1.set_title('original')
    
    # 2つ目の波形のプロット設定
    line2, = ax2.plot(plotdata_delay)
    ax2.set_ylim([-1.0, 1.0])
    ax2.set_xlim([0, BUFFER_SIZE])
    ax2.yaxis.grid(True)
    ax2.set_title('delay')
    
    # 3つ目の波形（掛け算）の設定を追加
    line3, = ax3.plot(plotdata_multiply)
    ax3.set_ylim([-1.0, 1.0])
    ax3.set_xlim([0, BUFFER_SIZE])
    ax3.yaxis.grid(True)
    ax3.set_title('multiply')
    
    lines = [line1, line2, line3]
    fig.tight_layout()
    return fig, lines

# メイン処理
setup_audio_device()
fig, lines = setup_plot()

# オーディオストリームとアニメーションの設定
stream = sd.InputStream(
    channels=1,
    dtype='float32',
    callback=audio_callback
)
animation = FuncAnimation(fig, update_plot, interval=30, blit=True)

# ストリーム開始とプロット表示
with stream:
    plt.show()