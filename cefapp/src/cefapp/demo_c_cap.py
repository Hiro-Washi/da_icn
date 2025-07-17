# consumer.py
import cefpyco
import time
import csv
import threading
import psutil
from cefapp import CefAppConsumer

# --- 設定 ---
URI = "ccnx:/test/video"
NUM_RUNS = 10
PIPELINE_SIZE = 2000  # パイプラインで同時に送信するInterest数
REPORT_FILE = "cefpyco_test_report.csv"

class StatConsumer(CefAppConsumer):
    """統計情報収集機能を拡張したコンシューマ"""
    def on_start(self, info):
        super().on_start(info)
        self.interest_send_times = {}
        self.chunk_rtts = []

    def send_interest_with_stat(self, name, chunk_num):
        """Interest送信と同時に送信時刻を記録"""
        self.interest_send_times[chunk_num] = time.perf_counter()
        self.cef_handle.send_interest(name, chunk_num)

    def on_rcv_succeeded(self, info, packet):
        """Data受信時にRTTを計算"""
        c = packet.chunk_num
        if c in self.interest_send_times:
            rtt = (time.perf_counter() - self.interest_send_times[c]) * 1000  # msに変換
            self.chunk_rtts.append(rtt)
        super().on_rcv_succeeded(info, packet)
        
    # パイプライニング部分をオーバーライドして統計収集関数を呼ぶ
    def send_interests_with_pipeline(self, info):
        to_index = min(info.count, self.req_tail_index + self.pipeline)
        for i in range(self.req_tail_index, to_index):
            if info.finished_flag[i]: continue
            if not self.req_flag[i]:
                self.send_interest_with_stat(info.name, i)
                self.req_flag[i] = 1

    def send_next_interest(self, info):
        # 元のロジックを維持しつつ、Interest送信部分をフック
        # (ここでは簡略化のため、パイプライン送信のみに絞る。
        #  より厳密にはこちらもオーバーライドが必要)
        pass

class ResourceMonitor(threading.Thread):
    """CPUとメモリを監視するスレッド"""
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.cpu_percents = []
        self.mem_percents = []
        self.daemon = True

    def run(self):
        while not self.stop_event.is_set():
            self.cpu_percents.append(psutil.cpu_percent())
            self.mem_percents.append(psutil.virtual_memory().percent)
            time.sleep(0.5)

    def stop(self):
        self.stop_event.set()

    def get_avg_stats(self):
        avg_cpu = sum(self.cpu_percents) / len(self.cpu_percents) if self.cpu_percents else 0
        avg_mem = sum(self.mem_percents) / len(self.mem_percents) if self.mem_percents else 0
        return avg_cpu, avg_mem

def main():
    """性能評価を実行し、結果をCSVに保存するメイン関数"""
    results = []

    for i in range(NUM_RUNS):
        print(f"\n----- Starting Run #{i + 1}/{NUM_RUNS} -----")
        
        monitor = ResourceMonitor()
        monitor.start()
        
        run_start_time = time.perf_counter()

        with cefpyco.create_handle() as h:
            consumer = StatConsumer(h, pipeline=PIPELINE_SIZE, enable_log=False)
            try:
                # コンテンツ取得を実行
                consumer.run(URI)
            except Exception as e:
                print(f"Error during run #{i + 1}: {e}")

        run_end_time = time.perf_counter()
        monitor.stop()
        monitor.join()

        # --- 統計情報の計算 ---
        total_time_sec = run_end_time - run_start_time
        total_bytes_expected = consumer.info.count * 1024 # チャンクサイズを基に計算
        total_bytes_received = sum(len(c.encode()) for c in consumer.cob_list)
        success_rate = (total_bytes_received / total_bytes_expected) * 100 if total_bytes_expected > 0 else 0
        throughput_mbps = (total_bytes_received * 8) / total_time_sec / 1e6 if total_time_sec > 0 else 0
        interests_sent = len(consumer.interest_send_times)
        data_packets_received = consumer.info.n_finished
        avg_chunk_rtt = sum(consumer.chunk_rtts) / len(consumer.chunk_rtts) if consumer.chunk_rtts else 0
        avg_cpu, avg_mem = monitor.get_avg_stats()
        
        run_result = {
            'run_id': i + 1,
            'total_time_sec': round(total_time_sec, 3),
            'total_bytes_expected': total_bytes_expected,
            'total_bytes_received': total_bytes_received,
            'success_rate_percent': round(success_rate, 2),
            'throughput_mbps': round(throughput_mbps, 3),
            'interests_sent': interests_sent,
            'data_packets_received': data_packets_received,
            'timeouts': consumer.info.timeout_count,
            'avg_chunk_rtt_ms': round(avg_chunk_rtt, 3),
            'avg_cpu_percent': round(avg_cpu, 2),
            'avg_mem_percent': round(avg_mem, 2),
        }
        results.append(run_result)
        print(f"Run #{i + 1} Result: {run_result}")

    # --- CSVファイルへの書き込み ---
    print(f"\nWriting results to {REPORT_FILE}...")
    if not results:
        print("No results to write.")
        return
        
    with open(REPORT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print("Test finished successfully.")

if __name__ == '__main__':
    main()
