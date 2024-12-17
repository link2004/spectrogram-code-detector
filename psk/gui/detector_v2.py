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

## 波の設定
WAVES = [
    {"frequency": 4410, "switch_interval": 55, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
    {"frequency": 3308, "switch_interval": 41, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
    {"frequencay": 2205, "switch_interval": 28, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
]


## ゲイン
TARGET_MAX = 0.8  # 目標最大値
GAIN_INCREASE_RATE = 0.01  # 共通の増加率
GAIN_DECREASE_RATE = 0.8   # 共通の減少率

# 初期化を変更
current_gains = [wave["initial_gain"] for wave in WAVES]

## パラメータ
SAMPLE_RATE = 44100   
BUFFER_SIZE = int(0.5 * SAMPLE_RATE)  

# 各波形用のバッファを作成
plotdata_originals = [np.zeros((BUFFER_SIZE)) for _ in WAVES]
plotdata_delays = [np.zeros((SAMPLE_RATE // wave["frequency"] * wave["switch_interval"] + BUFFER_SIZE)) for wave in WAVES]
plotdata_multiplies = [np.zeros((BUFFER_SIZE)) for _ in WAVES]

# バンドパスフィルタの設定を追加
def create_bandpass_filter(center_freq, bandwidth):
    """中心周波数とバンド幅でバンドパスフィルタを作成する"""
    nyquist = SAMPLE_RATE * 0.5
    low = (center_freq - bandwidth / 2) / nyquist
    high = (center_freq + bandwidth / 2) / nyquist
    b, a = signal.butter(6, [low, high], btype='band')
    return b, a

def audio_callback(indata, frames, time, status):
    """オーディオ入力コールバック関数"""
    global plotdata_originals, plotdata_delays, plotdata_multiplies, current_gains
    data = indata[:, 0]
    
    for i, wave in enumerate(WAVES):
        # バンドパスフィルタを適用（周波数ごとのバンド幅を使用）
        b, a = create_bandpass_filter(wave["frequency"], wave["bandwidth"])
        filtered_data = signal.filtfilt(b, a, data)

        # ゲインの自動調整（共通のレート使用）
        current_max = np.max(np.abs(filtered_data))
        if current_max > 0:
            target_gain = min(TARGET_MAX / current_max, wave["max_gain"])
            adjust_rate = GAIN_INCREASE_RATE if target_gain > current_gains[i] else GAIN_DECREASE_RATE
            current_gains[i] = current_gains[i] * (1 - adjust_rate) + target_gain * adjust_rate

        # ゲインを適用
        filtered_data = filtered_data * current_gains[i]
        
        # メディアンフィルタのカーネルサイズを周波数に応じて調整
        kernel_size = max(3, min(5, int(SAMPLE_RATE / wave["frequency"] * 2)))
        if kernel_size % 2 == 0:
            kernel_size += 1
        filtered_data = signal.medfilt(filtered_data, kernel_size=kernel_size)
        
        shift = len(data)
        delay_samples = SAMPLE_RATE // wave["frequency"] * wave["switch_interval"]
        
        plotdata_originals[i] = np.roll(plotdata_originals[i], -shift)
        plotdata_originals[i][-shift:] = filtered_data
        
        plotdata_delays[i] = np.roll(plotdata_delays[i], -shift)
        plotdata_delays[i][-shift:] = filtered_data
        
        plotdata_multiplies[i] = np.roll(plotdata_multiplies[i], -shift)
        plotdata_multiplies[i][-shift:] = filtered_data * plotdata_delays[i][BUFFER_SIZE-shift:BUFFER_SIZE] * 4

def update_plot(frame):
    """プロット更新用コールバック関数"""
    for i in range(len(WAVES)):
        lines[i*3].set_ydata(plotdata_originals[i])
        lines[i*3 + 1].set_ydata(plotdata_multiplies[i])
        lines[i*3 + 2].set_text(f'Gain: {current_gains[i]:.2f}')
    return lines

def setup_plot():
    """プロットの初期設定を行う"""
    fig, axes = plt.subplots(len(WAVES), 2, figsize=(8, 4*len(WAVES)))
    lines = []
    
    for i, wave in enumerate(WAVES):
        # 1つ目の波形のプロット設定
        line1, = axes[i,0].plot(plotdata_originals[i])
        axes[i,0].set_ylim([-1.0, 1.0])
        axes[i,0].set_xlim([0, BUFFER_SIZE])
        axes[i,0].yaxis.grid(True)
        axes[i,0].set_title(f'original {wave["frequency"]}Hz')
        
        gain_text = axes[i,0].text(0.02, 0.95, f'Gain: {current_gains[i]:.2f}', 
                            transform=axes[i,0].transAxes,
                            bbox=dict(facecolor='white', alpha=0.7))
        
        # delay波形の表示を削除し、multiply波形を2列目に移動
        line2, = axes[i,1].plot(plotdata_multiplies[i])
        axes[i,1].set_ylim([-1.0, 1.0])
        axes[i,1].set_xlim([0, BUFFER_SIZE])
        axes[i,1].yaxis.grid(True)
        axes[i,1].set_title(f'multiply {wave["frequency"]}Hz')
        
        # linesリストからdelay波形関連を削除
        lines.extend([line1, line2, gain_text])
    
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