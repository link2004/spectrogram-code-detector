# Spectrogram Code Detector

音声信号を使ってテキストデータを送受信する実験プロジェクト。
キーボードで打った文字をPSK（位相偏移変調）で音に変換し、マイクで受信してテキストに復号する。

## プロジェクトの目的

音声変復調技術（PSK, FSK, 周波数マッピング等）の研究・実験。
複数のアプローチを試しながら段階的に発展してきた。

## 現在アクティブなコード

**送信側**: `psk/keyboard_psk.py`
- キーボード入力 → 7bit ASCII + パリティビット → 16bit化 → 4チャンネルPSK信号として音声出力

**受信側**: `psk/gui/detector_v3.py`
- マイクから4周波数のPSK信号をリアルタイム検出 → ビット復号 → パリティチェック

```
[キーボード入力]
      |
      v
keyboard_psk.py  (送信)
  文字 → 7bit ASCII + パリティ → 16bit → 4x4bit
      |
      v
  4つの搬送波に PSK 変調して音声出力
  (4410Hz, 3308Hz, 2756Hz, 2205Hz)
      |
      v  (スピーカー → マイク)
      |
detector_v3.py  (受信)
  バンドパスフィルタ → 遅延乗算復調 → ビット検出 → パリティチェック
      |
      v
[テキスト復号]
```

## ディレクトリ構成

```
spectrogram-code-detector/
│
├── psk/                          [Active] PSK変復調システム
│   ├── keyboard_psk.py           * 送信: キーボード入力 → PSK音声出力
│   ├── pskgenerator.py           * PSK信号生成エンジン (keyboard_psk.pyから利用)
│   ├── pskdetector_pureData.py   * WAVファイルからのPSK復調
│   ├── main.py                     E2Eテスト (信号生成 → 検出 → BER計算)
│   ├── pskgeneratorGui.py          GUI版PSKジェネレータ (tkinter)
│   ├── test.py                     テスト用スクリプト
│   │
│   ├── gui/                      [Active] リアルタイム受信・可視化
│   │   ├── detector_v3.py        * 最新: 4周波数同時検出 + パリティチェック
│   │   ├── detector.py             参考: v1 単一周波数版
│   │   └── detector_v2.py          参考: v2 (削除済み、git履歴に残存)
│   │
│   ├── fsk/                        FSK変調の実験
│   │   └── generate.py              FSK信号生成 (19kHz/20kHz)
│   │
│   └── archive/                    アーカイブ済みの旧コード
│       └── pskdetector.py           旧PSK検出器 (tkinter版)
│
├── comfortable_tone/             [Legacy] 和音ペアによる文字エンコード実験
│   ├── code_detector.py            2音の組み合わせから文字を検出
│   ├── tone.py                     キーボード → MIDI音出力
│   ├── sine.py                     キーボード → サイン波出力
│   ├── tone_sine.py                キーボード → デュアル周波数サイン波
│   ├── play_sine.py                サイン波生成ユーティリティ
│   ├── wariate.py                  エンコード式の全組み合わせ検証
│   └── test.py                     エンコード計算テスト
│
├── code_tone_encoder/            [Demo] Web版トーンエンコーダ
│   └── index.html                  文字 → 周波数トーン (Web Audio API)
│
├── typing_tone_generator/        [Demo] Web版タイピングトーン
│   └── index.html                  ボタン押下 → トーン再生 (Web Audio API)
│
├── code_detector.py              [Legacy] ルート直下の初期版検出器
├── spectrogram.py                [Legacy] リアルタイムスペクトログラム表示
├── amplitude_graph.py            [Legacy] リアルタイム振幅波形表示
└── frequency_graph.py            [Legacy] リアルタイム周波数スペクトル表示
```

**凡例**: `*` = 現在メインで使うファイル / [Active] [Legacy] [Demo] = 状態ラベル

## クイックスタート

### 必要なライブラリ

```bash
pip install numpy scipy sounddevice matplotlib keyboard pyaudio
```

### 送信（PC-A）

```bash
cd psk
python keyboard_psk.py
```

キーボードで文字を打つとPSK変調された音が出力される。

### 受信（PC-BまたはPC-A自身のマイク）

```bash
cd psk/gui
python detector_v3.py
```

4チャンネルのPSK信号をリアルタイムで検出・可視化する。

## 技術詳細

### PSK変調方式

1. 文字を7bit ASCIIに変換し、パリティビットを付加（8bit）
2. 8bitを2回繰り返して16bitに拡張（冗長性確保）
3. 16bitを4bitずつ4チャンネルに分割
4. 各チャンネルを異なる搬送波周波数でBPSK変調

| チャンネル | 周波数 (Hz) | スイッチ間隔 (周期数) |
|-----------|-------------|---------------------|
| 1         | 4410        | 110                 |
| 2         | 3308        | 82                  |
| 3         | 2756        | 68                  |
| 4         | 2205        | 56                  |

### 復調方式（detector_v3.py）

1. バンドパスフィルタで各チャンネルを分離
2. 受信信号と遅延信号の乗算で位相変化を検出
3. 適応ゲイン制御でダイナミックレンジを維持
4. しきい値判定でビット列を復号
5. パリティチェックでエラー検出

## 開発の経緯

| 時期 | フェーズ | 内容 |
|------|---------|------|
| 2024/05 | 初期実験 | 周波数-文字マッピングによるトーン検出 (ルート直下のファイル群) |
| 2024/06 | Web版 | ブラウザでトーン生成 (code_tone_encoder/, typing_tone_generator/) |
| 2024/09 | PSK導入 | PSK変復調の実装開始 (psk/) |
| 2024/10 | 和音実験 | 2音ペアによる文字エンコード (comfortable_tone/) |
| 2024/12 | PSK改良 | GUI付きリアルタイム検出、v1→v2→v3と進化 |
| 2024/12 | 最新 | 4周波数同時検出 + パリティチェック (detector_v3.py) |

## 使用技術

- **音声I/O**: PyAudio, sounddevice
- **信号処理**: NumPy, SciPy (FFT, バンドパスフィルタ)
- **可視化**: matplotlib, PyQtGraph
- **GUI**: tkinter (PSKジェネレータ), PyQt5 (スペクトログラム)
- **Web**: Web Audio API (デモ用)
- **入力**: keyboard, pynput
