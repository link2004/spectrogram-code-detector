import sounddevice as sd
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from scipy import signal
from typing import List

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
    {"frequency": 4410, "switch_interval": 110, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
    {"frequency": 3308, "switch_interval": 82, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
    {"frequency": 2756, "switch_interval": 68, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
    {"frequency": 2205, "switch_interval": 56, "initial_gain": 100, "max_gain": 500, "bandwidth": 441},
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

def detect_bits(data: np.ndarray, delay_samples: int) -> List[int]:
    """
    入力データから4ビットのデータを検出する
    
    Args:
        data: すでに掛け合わされた入力データ配列
        delay_samples: 遅延サンプル数
    
    Returns:
        List[int]: 検出された4ビットのデータ
    """
    # データ長が足りない場合は空リストを返す
    if len(data) < delay_samples * 5:  # 4ビット+1ビット分のバッファ
        return []
    
    # 5ビット分のデータ範囲ごとの和を計算
    bit_sums = np.array([
        np.sum(data[i*delay_samples:(i+1)*delay_samples]) 
        for i in range(5)  # 5ビット分計算
    ])
    
    # しきい値を設定して1ビットデータに変換
    threshold = np.mean([np.max(bit_sums), np.min(bit_sums)])
    bit_data = (bit_sums <= threshold).astype(int)
    
    return bit_data[:4].tolist()  # 最初の4ビットのみ返す

DETECT_THRESHOLD = 0.1
TARGET_DATA_BUFFER_SIZE = [SAMPLE_RATE // WAVES[i]["frequency"] * WAVES[i]["switch_interval"] * 5 for i in range(len(WAVES))]  # 4ビット+1ビット分に変更
target_data_buffers = [np.zeros((TARGET_DATA_BUFFER_SIZE[i])) for i in range(len(WAVES))]

def audio_callback(indata, frames, time, status):
    """オーディオ入力コールバック関数"""
    global plotdata_originals, plotdata_delays, plotdata_multiplies, current_gains, target_data_buffers
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
        
        # # メディアンフィルタのカーネルサイズを周波数に応じて調整
        # kernel_size = max(3, min(5, int(SAMPLE_RATE / wave["frequency"] * 2)))
        # if kernel_size % 2 == 0:
        #     kernel_size += 1
        # filtered_data = signal.medfilt(filtered_data, kernel_size=kernel_size)
        
        shift = len(data)
        
        plotdata_originals[i] = np.roll(plotdata_originals[i], -shift)
        plotdata_originals[i][-shift:] = filtered_data
        
        plotdata_delays[i] = np.roll(plotdata_delays[i], -shift)
        plotdata_delays[i][-shift:] = filtered_data
        
        plotdata_multiplies[i] = np.roll(plotdata_multiplies[i], -shift)
        plotdata_multiplies[i][-shift:] = filtered_data * plotdata_delays[i][BUFFER_SIZE-shift:BUFFER_SIZE] * 4

    # 全ての波の閾値をチェック
    thresholds = []
    target_data_list = []
    for i, wave in enumerate(WAVES):
        delay_samples = SAMPLE_RATE // wave["frequency"] * wave["switch_interval"]
        target_data = plotdata_multiplies[i][-delay_samples*5:]
        target_data_list.append(target_data)
        threshold = np.mean(np.abs(target_data))
        thresholds.append(threshold > DETECT_THRESHOLD)
    # 全ての波が閾値を超えた場合にのみ出力
    detected_bits_list = []
    if all(thresholds):
        for i, wave in enumerate(WAVES):
            print(f"{wave['frequency']}Hz: {threshold}")
            detected_bits = detect_bits(plotdata_multiplies[i], delay_samples)
            detected_bits_list.append(detected_bits)
    
    # WAVESの長さと比較する（現在は4波）
    if len(detected_bits_list) >= len(WAVES):  # 5ではなくlen(WAVES)に修正
        print(detected_bits_list)
        # target_dataをバッファに保存
        target_data_buffers = target_data_list


def update_plot(frame):
    """プロット更新用コールバック関数"""
    for i in range(len(WAVES)):
        lines[i*4].set_ydata(plotdata_originals[i])
        lines[i*4 + 1].set_ydata(plotdata_multiplies[i])
        lines[i*4 + 2].set_text(f'Gain: {current_gains[i]:.2f}')
        lines[i*4 + 3].set_ydata(target_data_buffers[i])  # target_dataの表示を更新
    return lines

def setup_plot():
    """プロットの初期設定を行う"""
    fig, axes = plt.subplots(len(WAVES), 3, figsize=(12, 4*len(WAVES)))  # 3列に変更
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
        
        # multiply波形
        line2, = axes[i,1].plot(plotdata_multiplies[i])
        axes[i,1].set_ylim([-1.0, 1.0])
        axes[i,1].set_xlim([0, BUFFER_SIZE])
        axes[i,1].yaxis.grid(True)
        axes[i,1].set_title(f'multiply {wave["frequency"]}Hz')
        
        # target_data波形
        line3, = axes[i,2].plot(target_data_buffers[i])
        axes[i,2].set_ylim([-1.0, 1.0])
        axes[i,2].set_xlim([0, TARGET_DATA_BUFFER_SIZE[i]])
        axes[i,2].yaxis.grid(True)
        axes[i,2].set_title(f'target data {wave["frequency"]}Hz')
        
        lines.extend([line1, line2, gain_text, line3])
    
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