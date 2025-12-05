#!/bin/bash

# Optimize all existing videos for web streaming
# Run this script after deployment to optimize videos already in your system

set -e

echo "================================================"
echo "Optimizing Existing Videos for Web Streaming"
echo "================================================"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: FFmpeg is not installed!"
    echo "Please run: sudo apt-get install -y ffmpeg"
    exit 1
fi

# Directories
UPLOAD_DIR="/var/www/cloud-storage/uploads"
DOWNLOAD_DIR="/var/www/cloud-storage/downloads"
OPTIMIZED_DIR="/var/www/cloud-storage/static/optimized_videos"
THUMBNAIL_DIR="/var/www/cloud-storage/static/thumbnails"

# Create directories if they don't exist
mkdir -p "$OPTIMIZED_DIR"
mkdir -p "$THUMBNAIL_DIR"

# Function to optimize a single video
optimize_video() {
    local input_file="$1"
    local filename=$(basename "$input_file")
    local name_no_ext="${filename%.*}"
    local output_file="$OPTIMIZED_DIR/${name_no_ext}_optimized.mp4"
    local thumbnail_file="$THUMBNAIL_DIR/${name_no_ext}.jpg"
    
    # Skip if already optimized
    if [ -f "$output_file" ]; then
        echo "  ✓ Already optimized: $filename"
        return
    fi
    
    echo "  → Optimizing: $filename"
    
    # Optimize video with FFmpeg
    ffmpeg -i "$input_file" \
        -c:v libx264 \
        -preset fast \
        -crf 23 \
        -maxrate 5M \
        -bufsize 10M \
        -movflags +faststart \
        -c:a aac \
        -b:a 128k \
        -ar 44100 \
        -y \
        "$output_file" \
        2>/dev/null
    
    if [ -f "$output_file" ]; then
        # Get file sizes
        original_size=$(du -h "$input_file" | cut -f1)
        optimized_size=$(du -h "$output_file" | cut -f1)
        echo "  ✓ Done! Original: $original_size, Optimized: $optimized_size"
        
        # Generate thumbnail
        if [ ! -f "$thumbnail_file" ]; then
            ffmpeg -i "$input_file" \
                -ss 00:00:01 \
                -vframes 1 \
                -vf "scale=320:-1" \
                "$thumbnail_file" \
                2>/dev/null
            
            if [ -f "$thumbnail_file" ]; then
                echo "  ✓ Thumbnail generated"
            fi
        fi
    else
        echo "  ✗ Failed to optimize: $filename"
    fi
}

# Process videos in uploads directory
echo ""
echo "Checking uploads directory..."
if [ -d "$UPLOAD_DIR" ]; then
    video_count=0
    for video in "$UPLOAD_DIR"/*.{mp4,mkv,webm,avi,mov} 2>/dev/null; do
        if [ -f "$video" ]; then
            optimize_video "$video"
            ((video_count++))
        fi
    done
    
    if [ $video_count -eq 0 ]; then
        echo "  No videos found in uploads"
    else
        echo "  Processed $video_count videos"
    fi
else
    echo "  Upload directory not found"
fi

# Process videos in downloads directory
echo ""
echo "Checking downloads directory..."
if [ -d "$DOWNLOAD_DIR" ]; then
    video_count=0
    for video in "$DOWNLOAD_DIR"/*.{mp4,mkv,webm,avi,mov} 2>/dev/null; do
        if [ -f "$video" ]; then
            optimize_video "$video"
            ((video_count++))
        fi
    done
    
    if [ $video_count -eq 0 ]; then
        echo "  No videos found in downloads"
    else
        echo "  Processed $video_count videos"
    fi
else
    echo "  Download directory not found"
fi

# Set proper permissions
echo ""
echo "Setting permissions..."
sudo chown -R www-data:www-data "$OPTIMIZED_DIR" "$THUMBNAIL_DIR" 2>/dev/null || true
sudo chmod -R 755 "$OPTIMIZED_DIR" "$THUMBNAIL_DIR" 2>/dev/null || true

echo ""
echo "================================================"
echo "Optimization Complete!"
echo "================================================"
echo ""
echo "Optimized videos: $OPTIMIZED_DIR"
echo "Thumbnails: $THUMBNAIL_DIR"
echo ""
echo "All videos are now ready for ultra-fast playback!"
