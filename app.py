from flask import Flask, render_template, request, jsonify, send_from_directory, Response, session, redirect, url_for, send_file
import os
import downloader
import threading
import queue
import json
import cv2
from PIL import Image
from functools import wraps
import mimetypes
import subprocess
import database as db
from datetime import datetime
import pytz
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2024'

# Login credentials
VALID_EMAIL = 'Sameerkom16@gmail.com'
VALID_PASSWORD = 'Sameerkom16@123'

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
THUMBNAIL_FOLDER = 'static/thumbnails'
OPTIMIZED_FOLDER = 'static/optimized_videos'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(OPTIMIZED_FOLDER, exist_ok=True)

# Initialize database
db.init_db()

# Dictionary to store progress queues
progress_queues = {}


def optimize_video_for_web(input_path, output_path):
    """Ultra-fast video optimization with FFmpeg"""
    try:
        if not os.path.exists(output_path):
            print(f"Optimizing video: {input_path}")
            
            # Ultra-fast FFmpeg preset for maximum speed
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # ULTRA FAST encoding
                '-crf', '22',  # Slightly better quality
                '-maxrate', '8M',  # Higher bitrate for better quality
                '-bufsize', '16M',
                '-movflags', '+faststart+frag_keyframe',  # Enhanced faststart
                '-c:a', 'aac',
                '-b:a', '192k',  # Higher audio quality
                '-ar', '48000',
                '-threads', '0',  # Use all CPU threads
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Video optimized: {output_path}")
            return True
    except Exception as e:
        print(f"Error optimizing video: {e}")
        try:
            import shutil
            shutil.copy2(input_path, output_path)
        except:
            pass
    return False

def generate_video_thumbnail(video_path, output_path):
    """Generate thumbnail"""
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((320, 180), Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=90, optimize=True)
            return True
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
    return False

def format_indian_datetime(dt):
    """Format datetime in Indian format"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    else:
        dt = dt.astimezone(IST)
    
    # Indian format: DD/MM/YYYY, HH:MM AM/PM
    return dt.strftime('%d/%m/%Y, %I:%M %p')

def get_disk_space():
    """Get disk space information for the storage directory"""
    try:
        # Get disk usage for the application directory
        stat = shutil.disk_usage(os.path.dirname(os.path.abspath(__file__)))
        
        total = stat.total
        used = stat.used
        free = stat.free
        
        # Calculate percentage used
        percent_used = (used / total) * 100 if total > 0 else 0
        
        # Convert to human-readable format
        def format_bytes(bytes_val):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f} PB"
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent_used': round(percent_used, 1),
            'total_formatted': format_bytes(total),
            'used_formatted': format_bytes(used),
            'free_formatted': format_bytes(free)
        }
    except Exception as e:
        print(f"Error getting disk space: {e}")
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'percent_used': 0,
            'total_formatted': 'N/A',
            'used_formatted': 'N/A',
            'free_formatted': 'N/A'
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == VALID_EMAIL and password == VALID_PASSWORD:
            session['logged_in'] = True
            session['user_email'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    if 'logged_in' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Get sort preference
    sort_by = request.args.get('sort', db.get_user_preference('sort_by', 'date'))
    order = request.args.get('order', db.get_user_preference('sort_order', 'desc'))
    
    # Save preference
    if request.args.get('sort'):
        db.set_user_preference('sort_by', sort_by)
        db.set_user_preference('sort_order', order)
    
    # Get all files from database
    files_data = db.get_all_files(sort_by=sort_by, order=order)
    
    # Format files for display - ONLY if file exists on disk
    files = []
    files_to_delete = []  # Track missing files for cleanup
    
    for file_data in files_data:
        filepath = file_data['filepath']
        
        # ✅ CHECK: Only show file if it actually exists on disk
        if not os.path.exists(filepath):
            print(f"⚠️ File missing from disk: {filepath} (ID: {file_data['id']})")
            files_to_delete.append(file_data['id'])
            continue  # Skip this file
        
        file_info = {
            'id': file_data['id'],
            'name': file_data['filename'],
            'size': file_data['file_size'],
            'type': file_data['source_type'],
            'path': file_data['filepath'],
            'thumbnail': file_data['thumbnail_path'],
            'optimized': file_data['optimized_path'],
            'upload_date': format_indian_datetime(file_data['upload_date']),
            'upload_date_raw': file_data['upload_date'],
            'last_position': file_data.get('last_position', 0),
            'watch_percentage': file_data.get('watch_percentage', 0)
        }
        files.append(file_info)
    
    # Clean up database entries for missing files
    for file_id in files_to_delete:
        try:
            db.delete_file(file_id)
            print(f"🗑️ Cleaned up database entry for missing file ID: {file_id}")
        except Exception as e:
            print(f"❌ Error cleaning up file ID {file_id}: {e}")
    
    # Get disk space information
    disk_space = get_disk_space()
    
    return render_template('index.html', files=files, current_sort=sort_by, current_order=order, storage=disk_space)

@app.route('/history')
@login_required
def history():
    """Watch history page"""
    watch_history = db.get_all_watch_history()
    
    # Format for display - ONLY if file exists on disk
    history_items = []
    
    for item in watch_history:
        filepath = item['filepath']
        
        # ✅ CHECK: Only show file if it actually exists on disk
        if not os.path.exists(filepath):
            print(f"⚠️ History file missing from disk: {filepath}")
            continue  # Skip this file
        
        history_info = {
            'id': item['id'],
            'name': item['filename'],
            'size': item['file_size'],
            'type': item['source_type'],
            'thumbnail': item['thumbnail_path'],
            'optimized': item['optimized_path'],
            'last_position': item['last_position'],
            'duration': item['duration'],
            'watch_percentage': item['watch_percentage'],
            'last_watched': format_indian_datetime(item['last_watched'])
        }
        history_items.append(history_info)
    
    # Get disk space information
    disk_space = get_disk_space()
    
    return render_template('history.html', history=history_items, storage=disk_space)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Add to database
        file_size = os.path.getsize(filepath)
        file_type = filename.split('.')[-1].lower() if '.' in filename else None
        file_id = db.add_file(filename, filepath, 'upload', file_size, file_type)
        
        # Optimize video in background
        if filename.lower().endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov')):
            optimized_name = os.path.splitext(filename)[0] + '_optimized.mp4'
            optimized_path = os.path.join(OPTIMIZED_FOLDER, optimized_name)
            thumbnail_name = os.path.splitext(filename)[0] + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_name)
            
            def process_video():
                # Generate thumbnail
                if generate_video_thumbnail(filepath, thumbnail_path):
                    db.update_file_metadata(file_id, thumbnail_path=thumbnail_name)
                
                # Optimize video
                if optimize_video_for_web(filepath, optimized_path):
                    db.update_file_metadata(file_id, optimized_path=optimized_name)
            
            threading.Thread(target=process_video, daemon=True).start()
        
        return jsonify({'status': 'success', 'message': 'File uploaded successfully'})

@app.route('/download-url', methods=['POST'])
@login_required
def download_url():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'})
    
    import hashlib
    download_id = hashlib.md5(url.encode()).hexdigest()
    progress_queues[download_id] = queue.Queue()
    
    def progress_callback(downloaded, total, percent, status):
        if download_id in progress_queues:
            progress_queues[download_id].put({
                'downloaded': downloaded,
                'total': total,
                'percent': percent,
                'status': status
            })
    
    def run_download():
        result = downloader.download_video(url, DOWNLOAD_FOLDER, progress_callback)
        
        if result:
            filename = os.path.basename(result)
            file_size = os.path.getsize(result)
            file_type = filename.split('.')[-1].lower() if '.' in filename else None
            
            # Add to database
            file_id = db.add_file(filename, result, 'download', file_size, file_type)
            
            # Optimize video
            optimized_name = os.path.splitext(filename)[0] + '_optimized.mp4'
            optimized_path = os.path.join(OPTIMIZED_FOLDER, optimized_name)
            thumbnail_name = os.path.splitext(filename)[0] + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_name)
            
            # Generate thumbnail
            if generate_video_thumbnail(result, thumbnail_path):
                db.update_file_metadata(file_id, thumbnail_path=thumbnail_name)
            
            # Optimize
            if optimize_video_for_web(result, optimized_path):
                db.update_file_metadata(file_id, optimized_path=optimized_name)
        
        if download_id in progress_queues:
            progress_queues[download_id].put({
                'downloaded': 0,
                'total': 0,
                'percent': 100,
                'status': 'completed' if result else 'failed',
                'done': True
            })
    
    thread = threading.Thread(target=run_download)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'download_id': download_id})

@app.route('/progress/<download_id>')
@login_required
def progress(download_id):
    """Server-Sent Events for download progress"""
    def generate():
        if download_id not in progress_queues:
            yield f"data: {json.dumps({'error': 'Invalid download ID'})}\n\n"
            return
        
        q = progress_queues[download_id]
        
        while True:
            try:
                progress_data = q.get(timeout=30)
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                if progress_data.get('done'):
                    del progress_queues[download_id]
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'keepalive': True})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/files/<source_type>/<path:filename>')
@login_required
def serve_file(source_type, filename):
    """Serve files with HTTP Range support"""
    folder = UPLOAD_FOLDER if source_type == 'upload' else DOWNLOAD_FOLDER
    file_path = os.path.join(folder, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        return send_file(
            file_path,
            mimetype=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
            conditional=True
        )
    
    # Parse range
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if byte_range[1] else file_size - 1
    
    if start >= file_size or end >= file_size:
        return "Requested Range Not Satisfiable", 416
    
    length = end - start + 1
    
    with open(file_path, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    
    response = Response(
        chunk,
        status=206,
        mimetype=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
        direct_passthrough=True
    )
    
    response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = str(length)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    
    return response

@app.route('/update-watch-position', methods=['POST'])
@login_required
def update_watch_position():
    """Update video watch position"""
    data = request.json
    file_id = data.get('file_id')
    position = data.get('position', 0)
    duration = data.get('duration', 0)
    
    if file_id:
        db.update_watch_history(file_id, position, duration)
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Invalid file ID'})

@app.route('/get-watch-position/<int:file_id>')
@login_required
def get_watch_position(file_id):
    """Get video watch position"""
    history = db.get_watch_history(file_id)
    
    if history:
        return jsonify({
            'status': 'success',
            'position': history['last_position'],
            'duration': history['duration']
        })
    
    return jsonify({'status': 'success', 'position': 0, 'duration': 0})

@app.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    try:
        file_data = db.get_file_by_id(file_id)
        if not file_data:
            return jsonify({'status': 'error', 'message': 'File not found'})
        
        # Delete physical files
        if os.path.exists(file_data['filepath']):
            os.remove(file_data['filepath'])
        
        if file_data['thumbnail_path']:
            thumb_path = file_data['thumbnail_path'].replace('/static/', 'static/')
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
        if file_data['optimized_path']:
            opt_path = file_data['optimized_path'].replace('/static/', 'static/')
            if os.path.exists(opt_path):
                os.remove(opt_path)
        
        # Delete from database
        db.delete_file(file_id)
        
        return jsonify({'status': 'success', 'message': 'File deleted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
