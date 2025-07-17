# consumer.py
import cefpyco
import time
import csv
import math
import threading
import psutil

# --- 設定 ---
URI = "ccnx:/test/video"
META_URI = f"{URI}/meta"
NUM_RUNS = 2  # 試行回数（可変）
PIPELINE_SIZE = 2000
RECEIVE_TIMEOUT_MS = 1000  # 1秒
REPORT_FILE = "cefpyco_raw_report.csv"

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

def get_total_chunks(handle):
    """メタ情報を取得して総チャンク数を返す"""
    for _ in range(5): # 5回リトライ
        handle.send_interest(META_URI, 0)
        packet = handle.receive(timeout_ms=1000)
        if not packet.is_failed and packet.name == META_URI:
            return int(packet.payload_s)
    return -1

def run_single_test(handle):
    """1回のコンテンツ取得テストを実行し、統計情報を返す"""
    total_chunks = get_total_chunks(handle)
    if total_chunks == -1:
        print("Error: Could not resolve meta info.")
        return None

    received_chunks = [False] * total_chunks
    num_received = 0
    total_bytes_received = 0
    timeouts = 0
    
    # 統計情報
    interest_send_times = {}
    chunk_rtts = []
    interests_sent = 0

    next_chunk_to_request = 0
    
    run_start_time = time.perf_counter()

    while num_received < total_chunks:
        # パイプラインを満たすまでInterestを送信
        while (len(interest_send_times) < PIPELINE_SIZE and 
               next_chunk_to_request < total_chunks):
            chunk_num = next_chunk_to_request
            if not received_chunks[chunk_num]:
                handle.send_interest(URI, chunk_num)
                interest_send_times[chunk_num] = time.perf_counter()
                interests_sent += 1
            next_chunk_to_request += 1
        
        # パケットを受信
        packet = handle.receive(timeout_ms=RECEIVE_TIMEOUT_MS)

        if packet.is_failed:
            timeouts += 1
            print(f"Timeout occurred. ({timeouts})")
            # タイムアウトが多発する場合、パイプラインをリセットして再送信する戦略も考えられる
            if timeouts > 20: # 20回連続タイムアウトで異常とみなし中断
                print("Too many timeouts. Aborting this run.")
                break
            continue
        
        if packet.is_data and packet.name == URI:
            chunk_num = packet.chunk_num
            
            if not received_chunks[chunk_num]:
                received_chunks[chunk_num] = True
                num_received += 1
                total_bytes_received += len(packet.payload)
                
                # RTTを計算
                if chunk_num in interest_send_times:
                    rtt_ms = (time.perf_counter() - interest_send_times.pop(chunk_num)) * 1000
                    chunk_rtts.append(rtt_ms)
                
                # 進捗表示
                if num_received % 1000 == 0:
                    print(f"Progress: {num_received}/{total_chunks} chunks received...")

    run_end_time = time.perf_counter()
    
    # この回の実行結果をまとめる
    stats = {
        "total_time_sec": run_end_time - run_start_time,
        "total_chunks": total_chunks,
        "total_bytes_received": total_bytes_received,
        "interests_sent": interests_sent,
        "data_packets_received": num_received,
        "timeouts": timeouts,
        "avg_chunk_rtt_ms": sum(chunk_rtts) / len(chunk_rtts) if chunk_rtts else 0
    }
    return stats

def main():
    """性能評価のメインループ"""
    all_results = []
    
    for i in range(NUM_RUNS):
        print(f"\n----- Starting Run #{i + 1}/{NUM_RUNS} -----")
        
        monitor = ResourceMonitor()
        monitor.start()

        with cefpyco.create_handle() as handle:
            run_stats = run_single_test(handle)
        
        monitor.stop()
        monitor.join()

        if not run_stats:
            print(f"Run #{i + 1} failed.")
            continue

        # 最終的な統計情報を計算
        total_bytes_expected = run_stats["total_chunks"] * 1024
        success_rate = (run_stats["total_bytes_received"] / total_bytes_expected) * 100 if total_bytes_expected > 0 else 0
        throughput_mbps = (run_stats["total_bytes_received"] * 8) / run_stats["total_time_sec"] / 1e6 if run_stats["total_time_sec"] > 0 else 0
        avg_cpu, avg_mem = monitor.get_avg_stats()
        
        final_result = {
            'run_id': i + 1,
            'total_time_sec': round(run_stats["total_time_sec"], 3),
            'total_bytes_expected': total_bytes_expected,
            'total_bytes_received': run_stats["total_bytes_received"],
            'success_rate_percent': round(success_rate, 2),
            'throughput_mbps': round(throughput_mbps, 3),
            'interests_sent': run_stats["interests_sent"],
            'data_packets_received': run_stats["data_packets_received"],
            'timeouts': run_stats["timeouts"],
            'avg_chunk_rtt_ms': round(run_stats["avg_chunk_rtt_ms"], 3),
            'avg_cpu_percent': round(avg_cpu, 2),
            'avg_mem_percent': round(avg_mem, 2),
        }
        all_results.append(final_result)
        print(f"Run #{i + 1} Result: {final_result}")

    # --- CSVファイルへの書き込み ---
    print(f"\nWriting results to {REPORT_FILE}...")
    if all_results:
        with open(REPORT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print("Test finished successfully.")
    else:
        print("No results to write.")

if __name__ == '__main__':
    main()
