# Zenoh 高度検証Dockerプラットフォーム システム設計書

## 1. 概要

本ドキュメントは、`./da_icn/zenoh_docker_simulator` プロジェクトにおける、Zenohの様々な通信シナリオを高度に検証するための、Dockerベースのシミュレーションプラットフォームのシステム設計を定義する。

### 1.1. プロジェクト目標

- **宣言的な設定:** ユーザーが単一の設定ファイル（例: `config.yaml`）にシミュレーションのトポロジー、リソース、通信シナリオを記述するだけで、検証環境を構築できる。
- **柔軟なトポロジー:** P2Pメッシュ、クライアント/サーバー、ルーターネットワークなど、任意のネットワークトポロジーを簡単に構成できる。
- **リソース制御:** 各ノードのコンピュータリソース（CPU, メモリ）や、ノード間リンクのネットワークリソース（帯域、遅延、パケットロス）を細かく設定できる機能を提供する。
- **拡張可能なアプリケーション:** 基本的なZenoh通信パターン（Pub/Sub, Query等）を標準アプリとして提供しつつ、ユーザーが独自のアプリケーション（Pythonスクリプト等）を簡単に追加・実行できるフレームワークを構築する。
- **再現性と自動化:** 設定ファイルに基づき、シミュレーション環境の構築、実行、破棄を完全に自動化し、高い再現性を確保する。

## 2. システムアーキテクチャ

本プラットフォームは、「シミュレーション・オーケストレーター」という中核コンポーネントが、ユーザー定義の「設定ファイル」を解釈し、動的に「Docker Composeファイル」を生成してシミュレーション環境を構築するアーキテクチャを採用する。

```
+----------------------+      +--------------------------+      +--------------------------------+
|   User               |----->|   Configuration File     |----->|   Simulation Orchestrator      |
| (Defines Simulation) |      |   (e.g., config.yaml)    |      |   (Python Script: main.py)     |
+----------------------+      +--------------------------+      +--------------------------------+
                                                                                |
                                                               (Generates)      |
                                                                                v
+--------------------------------------------------------------------------+  +--------------------------+
| Docker Host                                                              |  | docker-compose.yaml      |
|                                                                          |  +--------------------------+
|  +------------------+       +------------------+       +------------------+
|  |   Zenoh Node 1   |-------|   Zenoh Node 2   |-------|   Zenoh Node 3   |  <-- (Simulated Network Links)
|  | (Container)      |       | (Container)      |       | (Container)      |
|  | - App Runner     |       | - App Runner     |       | - App Runner     |
|  +------------------+       +------------------+       +------------------+
|                                                                          |
+--------------------------------------------------------------------------+
```

- **Configuration File (`config.yaml`):** シミュレーションの全てを定義するYAMLファイル。トポロジー、ノード、リンク、実行アプリケーションなどを記述する。
- **Simulation Orchestrator (`main.py`):** `config.yaml` を読み込み、`docker-compose.yaml` を動的に生成するPythonスクリプト。各ノードのDockerfileのビルド、ネットワーク設定（`tc`コマンドによる帯域制御など）、アプリケーションの起動シーケンスを管理する。
- **Docker Environment:** オーケストレーターによって生成されたDockerコンテナ群。各コンテナはZenohノードとして機能し、指定されたアプリケーションを実行する。コンテナ間のネットワークは、`config.yaml` の定義に基づき、帯域や遅延がシミュレートされる。

## 3. 設定ファイル (`config.yaml`) 設計

ユーザーがシミュレーションを定義するための、直感的かつ強力なスキーマを設計する。

```yaml
# config.yaml (Example)
project_name: my_zenoh_simulation

topology:
  nodes:
    - id: router-1
      type: router # 'router' or 'client'
      resources:
        cpu: "0.5"
        memory: "256m"
      apps:
        - app_id: video-publisher

    - id: client-1
      type: client
      apps:
        - app_id: video-subscriber
          params:
            target_router: router-1

  links:
    - endpoints: [router-1, client-1]
      resources:
        bandwidth: "10mbit" # 帯域
        latency: "20ms"     # 遅延
        loss: "0.1%"        # パケットロス率

applications:
  - id: video-publisher
    type: custom # 'builtin' or 'custom'
    source: ./apps/video_publisher.py
    command: python3 video_publisher.py
    params:
      key: "demo/video/stream"
      rate: "30fps"

  - id: video-subscriber
    type: custom
    source: ./apps/video_subscriber.py
    command: python3 video_subscriber.py
    params:
      key: "demo/video/stream"
```

## 4. ディレクトリ構造

プロジェクトの拡張性と保守性を考慮したディレクトリ構造を定義する。

- **`zenoh_docker_simulator/`**
  - **`main.py`**: シミュレーション・オーケストレーターのメインスクリプト。
  - **`config.yaml`**: デフォルトのシミュレーション設定ファイル。
  - **`README.md`**: プロジェクトの説明と使用方法。
  - **`docker/`**:
    - `base/Dockerfile`: 全てのノードコンテナのベースとなるDockerfile。
    - `entrypoint.sh`: コンテナ起動時にネットワーク設定やアプリ実行を行うスクリプト。
  - **`apps/`**:
    - `builtin/`: 標準提供されるZenohアプリケーション（例: `publisher.py`, `subscriber.py`）。
    - `custom/`: ユーザーが配置するカスタムアプリケーション用のディレクトリ。
  - **`docs/`**:
    - `SYSTEM_DESIGN.md`: このドキュメント。
  - **`results/`**:
    - `{timestamp}/`: 各シミュレーションのログやデータ出力先。

## 5. 議論への回答

> 各ノードの実行処理内容（Zenohアプリ？）はユーザーに任せるか、プラットフォームシステムとして標準である程度用意しておくか。

**回答：ハイブリッドアプローチを採用する。**

1.  **標準提供 (Built-in):** データストリーミング(Pub/Sub)、Query/Replyなど、典型的で汎用的なユースケースに対応するアプリケーションを標準で提供する。これにより、ユーザーはすぐに基本的な検証を開始できる。
2.  **ユーザー定義 (Custom):** ユーザーが独自のPythonスクリプトやコンパイル済みバイナリを `apps/custom` ディレクトリに配置し、`config.yaml` で指定するだけで、シミュレーションに組み込めるフレームワークを提供する。

このアプローチにより、**「手軽さ」**と**「高度なカスタマイズ性」**を両立させ、幅広い検証ニーズに対応する。
