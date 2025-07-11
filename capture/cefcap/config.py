# 定数定義 (ICNポート, プロトコル名など)

# 監視対象のICNプロトコル名 (Pysharkでのレイヤー名)
# 使用しているCefore/CCNxのDissectorによって名前が異なる可能性があります
# 例: 'cefore', 'ccnx', 'ccn', 'ndn' など
ICN_PROTOCOL_LAYER_NAME = 'ccnx' # <-- ここを使用するプロトコル名に合わせる

# 監視対象のICNトラフィックをフィルタするためのディスプレイフィルタ
# 例: ICNプロトコルのポート番号が分かっている場合やEtherTypeなど
# Pysharkのディスプレイフィルタ構文を使用
# 9695(UDP/TCP): cefnetd デフォルト、9696(TCP): csmgrd デフォルト
# cefore: ce_type (Interest: 0x01, Data: 0x02)
ICN_DISPLAY_FILTER = f'{ICN_PROTOCOL_LAYER_NAME}' # ICNプロトコルレイヤーがあるパケット全て
# より具体的にフィルタする場合の例：
# ICN_DISPLAY_FILTER = f'{ICN_PROTOCOL_LAYER_NAME} or udp port 9695 or tcp port 9696'
# ICN_DISPLAY_FILTER = f'ethertype 0x800' # IPv4の場合など、基盤プロトコルでフィルタしてからICNレイヤーをチェック

# 統計集計時の名前正規化設定
# Trueの場合、名前を '/' で分割し、指定深度までのプレフィックスで集計
NORMALIZE_NAMES_BY_PREFIX = True
PREFIX_DEPTH_FOR_STATS = 3 # 例: /prefix/level1/level2/... の場合、3を指定すると /prefix/level1/level2/ で集計

# RTT計算のタイムアウト (秒) - Interest送信後、この時間を超えてもDataが来なければRTT計測失敗とみなす
RTT_TIMEOUT_SEC = 5.0

# RTT計算を有効にするか
ENABLE_RTT_CALCULATION = True
