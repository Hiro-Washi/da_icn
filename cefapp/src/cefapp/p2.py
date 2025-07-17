# producer.py
import os
import math
import cefpyco

# --- 設定 ---
URI = "ccnx:/test/video"
META_URI = f"{URI}/meta"
FILE_PATH = "video.mp4"
FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
CHUNK_SIZE = 1024  # 1024 Bytes

def create_dummy_file_if_not_exists():
    """100MBのダミーファイルが存在しない場合に生成する"""
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) != FILE_SIZE_BYTES:
        print(f"Creating a {FILE_SIZE_BYTES / 1024 / 1024:.0f}MB dummy file: {FILE_PATH}...")
        with open(FILE_PATH, 'wb') as f:
            f.write(b'\x00' * FILE_SIZE_BYTES)
        print("Dummy file created.")

def main():
    """プロデューサを起動するメイン関数"""
    create_dummy_file_if_not_exists()
    
    print(f"Reading content from {FILE_PATH}...")
    with open(FILE_PATH, 'rb') as f:
        content_data = f.read()

    total_chunks = math.ceil(FILE_SIZE_BYTES / CHUNK_SIZE)
    
    with cefpyco.create_handle() as handle:
        # 提供するコンテンツ名をcefdに登録
        handle.register(URI)
        
        print(f"Producer is running. Serving URI: {URI}")
        print(f"Total Chunks: {total_chunks}")
        print("Press Ctrl+C to stop.")

        while True:
            # Interestを待機
            packet = handle.receive()

            if packet.is_interest:
                # 通常のデータチャンク要求
                if packet.name == URI:
                    chunk_num = packet.chunk_num
                    if 0 <= chunk_num < total_chunks:
                        offset = chunk_num * CHUNK_SIZE
                        chunk = content_data[offset:offset + CHUNK_SIZE]
                        handle.send_data(URI, chunk, chunk_num, expiry=3600000, cache_time=3600000)
                        print(f"Sent chunk #{chunk_num}")

                # メタ情報（総チャンク数）の要求
                elif packet.name == META_URI:
                    handle.send_data(META_URI, str(total_chunks), 0)
                    print(f"Sent meta info: {total_chunks} chunks")

if __name__ == '__main__':
    main()
