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
SUMMARY_REPORT_FILE = "cefpyco_summary_report.csv"
TIMESERIES_LOG_FILE = "cefpyco_timeseries_log.csv" # 時系列ログファイル名

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
            try:
                return int(packet.payload_s)
            except (ValueError, TypeError):
                print(f"Error: Invalid meta info payload: {packet.payload_s}")
                return -1
    return -1

def run_single_test(handle, run_id, timeseries_log):
    """1回のコンテンツ取得テストを実行し、統計情報を返す"""
    total_chunks = get_total_chunks(handle)
    if total_chunks == -1:
        print("Error: Could not resolve meta info.")
        return None

    run_start_time = time.perf_counter()

    # 状態管理変数
    received_chunks = [False] * total_chunks
    num_received = 0
    total_bytes_received = 0
    timeouts = 0
    
    # 統計情報
    interest_send_times = {}
    chunk_rtts = []
    interests_sent = 0

    next_chunk_to_request = 0

    while num_received < total_chunks:
        # パイプラインを満たすまでInterestを送信
        while len(interest_send_times) < PIPELINE_SIZE and next_chunk_to_request < total_chunks:
            chunk_num = next_chunk_to_request
            if not received_chunks[chunk_num]:
                handle.send_interest(URI, chunk_num)
                current_time = time.perf_counter()
                interest_send_times[chunk_num] = current_time
                interests_sent += 1
                # 時系列ログにINTEREST_SENTイベントを追加
                timeseries_log.append({
                    'run_id': run_id,
                    'timestamp_sec': current_time - run_start_time,
                    'event_type': 'INTEREST_SENT',
                    'chunk_num': chunk_num,
                    'data_size_bytes': None,
                    'rtt_ms': None,
                })
            next_chunk_to_request += 1
        
        # パケットを受信
        packet = handle.receive(timeout_ms=RECEIVE_TIMEOUT_MS)

        if packet.is_failed:
            timeouts += 1
            # 時系列ログにTIMEOUTイベントを追加
            timeseries_log.append({
                'run_id': run_id,
                'timestamp_sec': time.perf_counter() - run_start_time,
                'event_type': 'TIMEOUT',
                'chunk_num': None,
                'data_size_bytes': None,
                'rtt_ms': None,
            })
            if timeouts > 20: 
                print("Too many timeouts. Aborting this run.")
                break
            continue
        
        if packet.is_data and packet.name == URI:
            chunk_num = packet.chunk_num
            
            if 0 <= chunk_num < total_chunks and not received_chunks[chunk_num]:
                received_chunks[chunk_num] = True
                num_received += 1
                payload_size = len(packet.payload)
                total_bytes_received += payload_size
                
                rtt_ms = None
                if chunk_num in interest_send_times:
                    rtt_ms = (time.perf_counter() - interest_send_times.pop(chunk_num)) * 1000
                    chunk_rtts.append(rtt_ms)
                
                # 時系列ログにDATA_RECEIVEDイベントを追加
                timeseries_log.append({
                    'run_id': run_id,
                    'timestamp_sec': time.perf_counter() - run_start_time,
                    'event_type': 'DATA_RECEIVED',
                    'chunk_num': chunk_num,
                    'data_size_bytes': payload_size,
                    'rtt_ms': round(rtt_ms, 3) if rtt_ms is not None else None,
                })
                
                if num_received % 1000 == 0:
                    print(f"Progress: {num_received}/{total_chunks} chunks received...")

    run_end_time = time.perf_counter()
    
    stats = {
        "total_time_sec": run_end_time - run_start_time,
        "total_chunks": total_chunks,
        "total_bytes_received": total_bytes_received,
        "interests_sent": interests_sent,
        "data_packets_received": num_received,
        "timeouts": timeouts,
        "avg_chunk_rtt_ms": sum(chunk_rtts) / len(chunk_rtts) if chunk_rtts else 0,
    }
    return stats

def main():
    """性能評価のメインループ"""
    summary_results = []
    timeseries_log = []
    
    for i in range(NUM_RUNS):
        print(f"\n----- Starting Run #{i + 1}/{NUM_RUNS} -----")
        
        monitor = ResourceMonitor()
        monitor.start()

        with cefpyco.create_handle() as handle:
            run_stats = run_single_test(handle, i + 1, timeseries_log)
        
        monitor.stop()
        monitor.join()

        if not run_stats:
            print(f"Run #{i + 1} failed.")
            continue

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
        summary_results.append(final_result)
        print(f"Run #{i + 1} Summary: {final_result}")

    # --- サマリーレポートCSVファイルへの書き込み ---
    print(f"\nWriting summary report to {SUMMARY_REPORT_FILE}...")
    if summary_results:
        with open(SUMMARY_REPORT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=summary_results[0].keys())
            writer.writeheader()
            writer.writerows(summary_results)
    else:
        print("No summary results to write.")
        
    # --- 時系列ログCSVファイルへの書き込み ---
    print(f"Writing time-series log to {TIMESERIES_LOG_FILE}...")
    if timeseries_log:
        with open(TIMESERIES_LOG_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=timeseries_log[0].keys())
            writer.writeheader()
            writer.writerows(timeseries_log)
    else:
        print("No time-series data to write.")
    
    print("\nTest finished successfully.")

if __name__ == '__main__':
    main()
