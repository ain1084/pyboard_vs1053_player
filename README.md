# pyboard_vs1053_player
(Japanese only)

## 概要

Pyboard から VS1053b を制御して MicroSD カード内の音楽ファイルを再生するものです。

![IMG_20210525_012613](https://user-images.githubusercontent.com/14823909/119379389-61960680-bcfa-11eb-983e-c5d256f107e5.jpg)

- VS1053b 搭載基板は [SparkFun MP3 and MIDI Breakout - VS1053](https://www.sparkfun.com/products/retired/9943)(現在は販売終了)です。
- VS1053b とは SPI と XCS, DREQ を接続します。SDISHARE のため XDCS は使用しません。 

## 動作方法

- 一応は [vs1053_player](https://github.com/ain1084/pyboard_vs1053_player/blob/main/vs1053_player) が package 本体です。
- テスト用の [test.py](https://github.com/ain1084/pyboard_vs1053_player/blob/main/test.py) を実装しています。
- REPL からは以下の入力で指定ディレクトリ内の音楽ファイルを再生します。
```
  import test
  test.start(directory)
```
- 例えば MicroSD カード内に音楽ファイルが入った music/ ディレクトリがある場合、directory へ 'music' を指定します。
- I2S 出力目的のため、アナログ音量の変更等は未実装です。LEFT および RIGHT ピンからはデフォルトの音量で出力されます。
- vs1053_player/VS1053 クラスは VS1053b の操作を実装しているクラスですが、利用していない宣言等はコメントアウトしています。
- Pyboard 上の USB ボタンを押すと再生中の曲をスキップできます。
- asyncio を利用していますが、run メソッドでブロックしているため、全ファイルの演奏が終了するまで戻ってきません。
  - 強制終了は Ctrl+C です。
- その他はコードを参照して下さい。 

## その他

- [max9850.py](https://github.com/ain1084/pyboard_vs1053_player/blob/main/max9850.py) は I2S DAC として接続した [maxim integrated MAX9850](https://www.maximintegrated.com/jp/products/analog/audio/MAX9850.html) の初期化を行うものです。
  - 前述の test.start の呼び出し前に一度だけ REPL から import max9850 して使用します。
  - 画像の左に写っている基板が MAX9850 の breakout (自作)です。
  - VS1053b からは x256Fs の MCLK が出力されますので、大抵の DAC はそのまま接続可能です。
