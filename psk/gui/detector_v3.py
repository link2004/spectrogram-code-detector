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

def detect_bits(bit_sums: np.ndarray) -> List[int]:
    """
    和からビットを検出する
    """

    # # 絶対値が一定の値を超えているか判定
    # threshold = 200
    # if np.mean(np.abs(bit_sums[:4])) > threshold:
    #     return [-1, -1, -1, -1]

    threshold = 0
    bit_data = (bit_sums <= threshold).astype(int)
    return bit_data[:4].tolist()  # 最初の4ビットのみ返す

def detect_sums(target_data: np.ndarray, delay_samples: int) -> np.ndarray:
    """
    入力データから5ビット分の和を計算する
    
    Args:
        target_data: すでに掛け合わされた入���データ配列
        delay_samples: 遅延サンプル数
        i: 波形のインデックス
    
    Returns:
        np.ndarray: 5ビット分の和の配列
    """
    # データ長が足りない場合は空配列を返す
    if len(target_data) < delay_samples * 5:  # 4ビット+1ビット分のバッファ
        return np.array([])
    
    # 5ビット分のデータ範囲ごとの和を計算
    bit_sums = np.array([
        np.sum(target_data[j*delay_samples:(j+1)*delay_samples]) 
        for j in range(5)  # 5ビット分計算
    ])


    return bit_sums

DETECT_THRESHOLD = 0.1
TARGET_DATA_BUFFER_SIZE = [SAMPLE_RATE // WAVES[i]["frequency"] * WAVES[i]["switch_interval"] * 5 for i in range(len(WAVES))]  # 4ビット+1ビット分に変更
target_data_buffers = [np.zeros((TARGET_DATA_BUFFER_SIZE[i])) for i in range(len(WAVES))]

bit_sums_buffers = [np.zeros(5) for _ in WAVES]  # 各波形のbit_sums用バッファ

def check_parity(bits: List[int]) -> bool:
    """
    8ビットのパリティチェックを行う
    最後のビットはパリティビット
    
    Args:
        bits: 8ビットのリスト
    
    Returns:
        bool: パリティチェックが正しければTrue
    """
    if len(bits) != 8:
        return False
    
    # 最後のビットを除いた7ビットの1の数を数える
    data_bits_sum = sum(bits[:7])
    # 偶数パリティの場合
    expected_parity = data_bits_sum % 2
    
    return bits[7] == expected_parity

def audio_callback(indata, frames, time, status):
    """オーディオ入力コールバック関数"""
    global plotdata_originals, plotdata_delays, plotdata_multiplies, current_gains, target_data_buffers, bit_sums_buffers
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

    # 各波形のデータを処理
    detected_bits_list = []
    detected_sums_list = []
    if all(thresholds):
        for i, wave in enumerate(WAVES):
            delay_samples = SAMPLE_RATE // wave["frequency"] * wave["switch_interval"]
            detected_sums = detect_sums(target_data_list[i], delay_samples)
            detected_bits = detect_bits(detected_sums)
            detected_sums_list.append(detected_sums)
            detected_bits_list.append(detected_bits)

        # 4ビットずつの配列を8ビットに結合
        if len(detected_bits_list) >= 2:
            # 最初の2つの波形の4ビットを結合して8ビットにする
            first_8bits = detected_bits_list[0] + detected_bits_list[1]
            # 次の2つの波形の4ビットを結合して8ビットにする
            second_8bits = detected_bits_list[2] + detected_bits_list[3]
            
            # パリティチェックを実行
            first_parity_ok = check_parity(first_8bits)
            second_parity_ok = check_parity(second_8bits)
            
            # パリティチェック結果を表示
            print(f"第1グループのパリティチェック結果: {'正常' if first_parity_ok else '異常'}")
            print(f"第2グループのパリティチェック結果: {'正常' if second_parity_ok else '異常'}")
            print(f"データ1: {first_8bits}, データ2: {second_8bits}")

            if first_parity_ok or second_parity_ok:
                bit_sums_buffers = detected_sums_list
                target_data_buffers = target_data_list
        


def update_plot(frame):
    """プロット更新用コールバック関数"""
    artists = []  # 更新するArtistオブジェクトを格納するリスト
    
    for i in range(len(WAVES)):
        # 波形とテキストの更新
        lines[i*5].set_ydata(plotdata_originals[i])
        lines[i*5 + 1].set_ydata(plotdata_multiplies[i])
        lines[i*5 + 2].set_text(f'Gain: {current_gains[i]:.2f}')
        lines[i*5 + 3].set_ydata(target_data_buffers[i])
        
        # Artist オブジェクトをリストに追加
        artists.extend([lines[i*5], lines[i*5 + 1], lines[i*5 + 2], lines[i*5 + 3]])
        
        # 棒グラフの更新
        for rect, val in zip(lines[i*5 + 4], bit_sums_buffers[i]):
            rect.set_height(val)
            artists.append(rect)  # 各棒をArtistリストに追加
    
    return artists  # 更新された全てのArtistオブジェクトのリストを返す

def setup_plot():
    """プロットの初期設定を行う"""
    fig, axes = plt.subplots(len(WAVES), 4, figsize=(16, 4*len(WAVES)))  # 4列に変更
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
        
        # bit_sums用の棒グラフの設定を変更
        line4 = axes[i,3].bar(range(5), bit_sums_buffers[i])
        axes[i,3].set_ylim([-500.0, 500.0])  # 範囲を-500から500に変更
        axes[i,3].set_xlim([-0.5, 4.5])
        axes[i,3].yaxis.grid(True)
        axes[i,3].set_title(f'bit sums {wave["frequency"]}Hz')
        
        lines.extend([line1, line2, gain_text, line3, line4])
    
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
animation = FuncAnimation(
    fig, 
    update_plot, 
    interval=30, 
    blit=True,
    cache_frame_data=False  # キャッシュを無効化
)

# ストリーム開始とプロット表示
with stream:
    plt.show()