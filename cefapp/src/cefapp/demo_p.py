# producer.py
import os
import cefpyco
from cefapp import CefAppProducer

# --- 設定 ---
URI = "ccnx:/test/video"
FILE_PATH = "video.mp4"
FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
CHUNK_SIZE = 1024  # 1024 Bytes

def create_dummy_file_if_not_exists():
    """100MBのダミーファイルが存在しない場合に生成する"""
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) != FILE_SIZE_BYTES:
        print(f"Creating a {FILE_SIZE_BYTES / 1024 / 1024:.0f}MB dummy file: {FILE_PATH}...")
        with open(FILE_PATH, 'wb') as f:
            f.write(os.urandom(FILE_SIZE_BYTES))
        print("Dummy file created.")

def main():
    """プロデューサを起動するメイン関数"""
    create_dummy_file_if_not_exists()
    
    print(f"Reading content from {FILE_PATH}...")
    with open(FILE_PATH, 'rb') as f:
        content_data = f.read()
    
    with cefpyco.create_handle() as handle:
        # プロデューサインスタンスを作成
        producer = CefAppProducer(
            handle,
            data=content_data,
            cob_len=CHUNK_SIZE,
            enable_log=True)
            
        print(f"Producer is running. Serving URI: {URI}")
        print("Press Ctrl+C to stop.")
        # 指定したURIでInterestを待ち受ける
        producer.run(URI)

if __name__ == '__main__':
    main()
