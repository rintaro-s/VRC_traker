## ⚠️本レポジトリのコメント及び変数名はAIによるものです。コメントと実際の動作は異なる場合があります
---
# VRC_traker

PCに接続されたカメラと両手のJoy-Conを使用し、上半身の動き（表情、手、手首）をトラッキングしてVRChatにOSCで送信するアプリケーションです。

## 概要

本プロジェクトは、以下のデータフローでVRChatへのトラッキングデータ送信を実現します。

*   **入力 (Input)**:
    *   **カメラ**: 顔の表情（目の開閉、口の開閉）、手の形状と位置（指の曲がり具合、ジェスチャー）を捉えます。
    *   **Joy-Con (左右)**: 手首の回転（ジャイロセンサー）と移動操作（スティック）、ジェスチャー切り替え（ボタン）の情報を取得します。
*   **処理 (Processing)**:
    *   カメラからの映像はMediaPipeを用いて顔と手のランドマークを検出します。
    *   Joy-Conからの生データは、VRChatのOSCパラメータに適した形式に変換されます。
    *   検出されたランドマークやJoy-Conのデータは、VRChatが解釈できるOSCメッセージに変換されます。
*   **出力 (Output)**:
    *   変換されたOSCメッセージは、VRChatのOSC機能を通じてアバターに適用され、リアルタイムな動きを再現します。

## 機能

*   **カメラトラッキング**: MediaPipeによる顔（目、口）と手（指のカーブ、ジェスチャー）の検出。
*   **Joy-Con連携**: 左右のJoy-Conからのジャイロ、スティック、ボタン入力の取得。
*   **OSC送信**: 検出・処理されたデータをVRChatへOSC経由で送信。
*   **GUI設定**: OSC接続情報、カメラID、トラッキングの閾値・感度などをリアルタイムで変更・保存可能なGUI。
*   **リアルタイム情報表示**: GUI上でカメラ映像プレビュー、Joy-Con接続状態、各トラッキングデータの詳細値を表示。
*   **3Dビジュアライザー**: 別ウィンドウで手のランドマークとJoy-Conの姿勢を簡易的な3Dモデルで可視化。

## 必要環境

*   **OS**: Windows (開発環境はWindowsを想定)
*   **Python**: Python 3.8以上 (推奨: Python 3.10)
*   **ハードウェア**:
    *   PCに接続可能なWebカメラ
    *   Bluetooth接続可能なNintendo Switch Joy-Con (左右)
    *   OpenGLをサポートするグラフィックカード (3Dビジュアライザー用)

## インストール

1.  **リポジトリのクローン**:
    ```bash
    git clone https://github.com/your-username/VRC_traker.git
    cd VRC_traker
    ```
    (もしGitを使用していない場合は、ZIPファイルをダウンロードして展開してください。)

2.  **Python環境の準備**:
    Pythonがインストールされていない場合は、[Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストールしてください。

3.  **必要なライブラリのインストール**:
    プロジェクトルートディレクトリで、以下のコマンドを実行します。
    ```bash
    pip install -r requirements.txt
    ```
    または、個別にインストールする場合:
    ```bash
    pip install opencv-python mediapipe python-osc joycon-python hidapi pyglm Pillow pyglet
    ```
    *   **注意**: `pyjoycon` の代わりに `joycon-python` を使用しています。

## 使用方法

1.  **Joy-Conのペアリング**:
    PCのBluetooth設定から、左右のJoy-Conをそれぞれペアリングしてください。

2.  **`settings.ini` の設定**:
    プロジェクトルートディレクトリにある `settings.ini` ファイルを開き、必要に応じて設定を調整してください。
    *   `[OSC]` セクション: VRChatのOSC受信設定に合わせて `host` と `port` を設定します。
    *   `[Camera]` セクション: 使用するカメラの `device_id` を設定します。通常は `0` ですが、複数カメラがある場合は変更が必要かもしれません。アプリケーションは自動検出を試みます。
    *   `[HandTracking]`, `[FaceTracking]`, `[JoyConTracking]` セクション: 各トラッキングの感度や閾値を調整できます。

3.  **アプリケーションの実行**:
    プロジェクトルートディレクトリで、以下のコマンドを実行します。
    ```bash
    "C:\Users\s-rin\AppData\Local\Programs\Python\Python310\python.exe" VRC_tracker/main.py
    ```
    *   `"C:\Users\s-rin\AppData\Local\Programs\Python\Python310\python.exe"` の部分は、ご自身のPython実行ファイルのフルパスに置き換えてください。

4.  **GUIの操作**:
    アプリケーションが起動すると、設定GUIと3Dビジュアライザーの2つのウィンドウが表示されます。
    *   **Settingsタブ**: 各種設定値を変更し、「Apply Settings」で適用、「Save Settings」で `settings.ini` に保存できます。
    *   **Real-time Infoタブ**: カメラ映像のプレビュー、Joy-Conの接続状態、検出されたトラッキングデータの詳細がリアルタイムで表示されます。
    *   **3D Visualizerウィンドウ**: 検出された手のランドマークとJoy-Conの姿勢が3Dで可視化されます。

## トラブルシューティング

*   **`ModuleNotFoundError: No module named '...'`**:
    *   `requirements.txt` に記載されているすべてのライブラリがインストールされているか確認してください。
    *   `pip install -r requirements.txt` を再度実行してみてください。
    *   `main.py` を実行しているPythonのパスが、ライブラリをインストールしたPythonのパスと一致しているか確認してください。上記「使用方法」の実行コマンドを参考に、Pythonのフルパスを明示的に指定してください。

*   **`pyglet.gl.lib.MissingFunctionException` (OpenGLエラー)**:
    *   お使いのグラフィックカードのドライバーを最新版に更新してください。
    *   PCに複数のグラフィックカードがある場合、高性能な方が使用されているか確認してください。

*   **カメラが検出されない**:
    *   `settings.ini` の `device_id` を確認してください。
    *   カメラがPCに正しく接続され、他のアプリケーションで使用されていないことを確認してください。
    *   アプリケーションは自動検出を試みますが、それでも検出されない場合は `device_id` を手動で `0`, `1`, `2` などと試してみてください。

*   **Joy-Conが接続されない**:
    *   Joy-ConがPCとBluetoothで正しくペアリングされているか確認してください。
    *   他のJoy-Con関連のソフトウェアがバックグラウンドで動作していないか確認してください。

## 今後の拡張

*   より高度な3Dモデルによる手の表示（指の関節の正確な曲げ伸ばしなど）。
*   顔の表情（笑顔、眉の動きなど）のより詳細なトラッキングとOSCパラメータへのマッピング。
*   Joy-Conの加速度センサーデータを用いた位置トラッキング。
*   GUIの機能強化（設定項目の詳細化、キャリブレーション機能など）。
