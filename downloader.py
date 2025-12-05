import os
import requests
import re
import time
from urllib.parse import urlparse, unquote
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ULTRA-OPTIMIZED settings for maximum speed
CHUNK_SIZE = 16 * 1024 * 1024  # 16MB chunks for ultra-fast downloads
MAX_RETRIES = 3  # Quick retries
TIMEOUT = 120  # Extended timeout
CONNECTION_TIMEOUT = 10  # Fast connection timeout
MAX_PARALLEL_CHUNKS = 8  # Download 8 chunks simultaneously
POOL_SIZE = 10  # Connection pool size

# Create a session pool for aggressive connection reuse
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=POOL_SIZE,
    pool_maxsize=POOL_SIZE,
    max_retries=0,  # Handle retries manually
    pool_block=False
)
session.mount('http://', adapter)
session.mount('https://', adapter)

session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1'
})

def get_filename_from_cd(cd):
    """Get filename from content-disposition"""
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return unquote(fname[0].strip().strip('"').strip("'"))

def download_chunk(url, start, end, chunk_num, output_file, progress_lock, downloaded_bytes, progress_callback):
    """Download a single chunk of the file"""
    headers = session.headers.copy()
    headers['Range'] = f'bytes={start}-{end}'
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=headers, stream=True, timeout=(CONNECTION_TIMEOUT, TIMEOUT))
            response.raise_for_status()
            
            chunk_data = b''
            for data in response.iter_content(chunk_size=1024*1024):  # 1MB read chunks
                if data:
                    chunk_data += data
                    
                    with progress_lock:
                        downloaded_bytes[0] += len(data)
                        if progress_callback:
                            progress_callback(downloaded_bytes[0], None, None, 'Downloading...')
            
            # Write chunk to file at correct position
            with open(output_file, 'r+b') as f:
                f.seek(start)
                f.write(chunk_data)
            
            return True
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"Chunk {chunk_num} failed after {MAX_RETRIES} attempts: {e}")
                return False
    
    return False

def download_video_parallel(url, output_folder, progress_callback=None):
    """
    Download video with parallel chunk downloading for ULTRA-FAST speed
    """
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        if progress_callback:
            progress_callback(0, 0, 0, 'Connecting...')
        
        # Get file info
        head_response = session.head(url, timeout=CONNECTION_TIMEOUT, allow_redirects=True)
        total_size = int(head_response.headers.get('content-length', 0))
        
        # Check if server supports range requests
        accept_ranges = head_response.headers.get('Accept-Ranges', '')
        supports_ranges = accept_ranges.lower() == 'bytes'
        
        # Get filename
        filename = None
        content_disposition = head_response.headers.get('Content-Disposition')
        if content_disposition:
            filename = get_filename_from_cd(content_disposition)
        
        if not filename:
            parsed_url = urlparse(url)
            filename = unquote(os.path.basename(parsed_url.path))
            if '?' in filename:
                filename = filename.split('?')[0]
        
        if not filename or filename == '':
            filename = f"download_{int(time.time())}.mp4"
        
        filepath = os.path.join(output_folder, filename)
        
        # If server doesn't support ranges or file is small, download normally
        if not supports_ranges or total_size < CHUNK_SIZE:
            return download_video_simple(url, output_folder, progress_callback)
        
        # Create empty file of the correct size
        with open(filepath, 'wb') as f:
            f.seek(total_size - 1)
            f.write(b'\0')
        
        # Calculate chunks
        chunk_ranges = []
        num_chunks = min(MAX_PARALLEL_CHUNKS, (total_size + CHUNK_SIZE - 1) // CHUNK_SIZE)
        chunk_size = total_size // num_chunks
        
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < num_chunks - 1 else total_size - 1
            chunk_ranges.append((start, end, i))
        
        # Progress tracking
        progress_lock = threading.Lock()
        downloaded_bytes = [0]
        
        if progress_callback:
            progress_callback(0, total_size, 0, f'Downloading with {num_chunks} connections...')
        
        # Download chunks in parallel
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CHUNKS) as executor:
            futures = []
            for start, end, chunk_num in chunk_ranges:
                future = executor.submit(
                    download_chunk,
                    url, start, end, chunk_num, filepath,
                    progress_lock, downloaded_bytes, progress_callback
                )
                futures.append(future)
            
            # Wait for all chunks
            all_success = True
            for future in as_completed(futures):
                if not future.result():
                    all_success = False
        
        if all_success:
            if progress_callback:
                progress_callback(total_size, total_size, 100, 'completed')
            print(f"Download completed: {filepath}")
            return filepath
        else:
            # Fallback to simple download if parallel failed
            os.remove(filepath)
            return download_video_simple(url, output_folder, progress_callback)
            
    except Exception as e:
        print(f"Parallel download error: {e}")
        # Fallback to simple download
        return download_video_simple(url, output_folder, progress_callback)

def download_video_simple(url, output_folder, progress_callback=None):
    """
    Simple download method (fallback)
    """
    os.makedirs(output_folder, exist_ok=True)
    
    for attempt in range(MAX_RETRIES):
        try:
            if progress_callback:
                progress_callback(0, 0, 0, f'Connecting... (Attempt {attempt + 1}/{MAX_RETRIES})')
            
            response = session.get(url, stream=True, timeout=(CONNECTION_TIMEOUT, TIMEOUT), allow_redirects=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Get filename
            filename = None
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                filename = get_filename_from_cd(content_disposition)
            
            if not filename:
                parsed_url = urlparse(url)
                filename = unquote(os.path.basename(parsed_url.path))
                if '?' in filename:
                    filename = filename.split('?')[0]
            
            if not filename or filename == '':
                filename = f"download_{int(time.time())}.mp4"
            
            filepath = os.path.join(output_folder, filename)
            
            # Download
            downloaded = 0
            if progress_callback:
                progress_callback(0, total_size, 0, 'Downloading...')
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(downloaded, total_size, percent, 'Downloading...')
            
            if progress_callback:
                progress_callback(downloaded, total_size, 100, 'completed')
            
            print(f"Download completed: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))
                continue
            else:
                if progress_callback:
                    progress_callback(0, 0, 0, f'failed: {str(e)}')
                raise
    
    return None

# Main download function
def download_video(url, output_folder, progress_callback=None):
    """
    Main download function - tries parallel first, falls back to simple
    """
    return download_video_parallel(url, output_folder, progress_callback)

if __name__ == "__main__":
    # Test with the provided link
    test_url = "https://cdn.kink.com/whippedass/members/106201/shoot/106201_shoot_high.mp4?nva=1764842403&token=5f7a996eab9a488a0a4363e158bbe24f"
    
    def print_progress(downloaded, total, percent, status):
        if total:
            print(f"Progress: {percent:.1f}% ({downloaded}/{total} bytes) - {status}")
        else:
            print(f"Status: {status}")
    
    download_video(test_url, "downloads", print_progress)
