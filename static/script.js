// Global variables
let currentFileId = null;
let currentFileType = '';
let currentFileName = '';
let watchPositionInterval = null;

// Update sort info on page load
document.addEventListener('DOMContentLoaded', function () {
    updateSortInfo();
    setupVideoPlayer();
});

// Sort menu toggle
function toggleSortMenu() {
    const sortModal = document.getElementById('sort-modal');
    if (sortModal) {
        sortModal.classList.toggle('hidden');
    }
}

// Change sort order
function changeSortOrder(sortBy, order) {
    window.location.href = `/?sort=${sortBy}&order=${order}`;
}

// Update sort info banner
function updateSortInfo() {
    if (typeof CURRENT_SORT === 'undefined') return;

    const sortText = document.getElementById('sort-text');
    if (!sortText) return;

    const sortLabels = {
        'name_asc': 'Name (A-Z)',
        'name_desc': 'Name (Z-A)',
        'date_desc': 'Date (Newest First)',
        'date_asc': 'Date (Oldest First)',
        'type_asc': 'Type',
        'size_desc': 'Size (Largest First)',
        'size_asc': 'Size (Smallest First)'
    };

    const key = `${CURRENT_SORT}_${CURRENT_ORDER}`;
    sortText.textContent = `Sorted by ${sortLabels[key] || 'Date (Newest First)'}`;
}

// View Toggle
function switchView(view) {
    const container = document.getElementById('files-container');
    const viewIcons = document.querySelectorAll('.view-icon');

    viewIcons.forEach(icon => icon.classList.remove('active'));

    if (view === 'grid') {
        container.classList.remove('list-view');
        container.classList.add('grid-view');
        document.querySelector('.view-icon[onclick*="grid"]').classList.add('active');
    } else {
        container.classList.remove('grid-view');
        container.classList.add('list-view');
        document.querySelector('.view-icon[onclick*="list"]').classList.add('active');
    }
}

// FAB Menu Toggle
function toggleFabMenu() {
    const fabMenu = document.getElementById('fab-menu');
    if (fabMenu) {
        fabMenu.classList.toggle('hidden');
    }
}

// File Upload Handler
function handleFileUpload(input) {
    if (input.files.length > 0) {
        const formData = new FormData();
        formData.append('file', input.files[0]);

        showToast('Uploading file...');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast('File uploaded! Optimizing for ultra-fast playback...');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showToast('Upload failed: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred during upload.');
            });
    }
}

// URL Modal Functions
function openUrlModal() {
    const urlModal = document.getElementById('url-modal');
    if (urlModal) {
        urlModal.classList.remove('hidden');
        setTimeout(() => {
            const urlInput = document.getElementById('url-input');
            if (urlInput) {
                urlInput.focus();
            }
        }, 100);
    }
}

function closeUrlModal() {
    const urlModal = document.getElementById('url-modal');
    if (urlModal) {
        urlModal.classList.add('hidden');
    }
    const urlInput = document.getElementById('url-input');
    if (urlInput) {
        urlInput.value = '';
    }
}

// Progress Bar Functions
function showProgressBar() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.classList.remove('hidden');
    }
}

function hideProgressBar() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.classList.add('hidden');
    }
}

function updateProgress(percent, status) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');

    if (progressBar) progressBar.style.width = percent + '%';
    if (progressText) progressText.textContent = Math.round(percent) + '%';
    if (progressStatus) progressStatus.textContent = status;
}

// Submit URL Download
function submitUrlDownload() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput ? urlInput.value : '';

    if (!url) {
        showToast('Please enter a URL');
        return;
    }

    fetch('/download-url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                closeUrlModal();
                showProgressBar();

                const downloadId = data.download_id;
                const eventSource = new EventSource(`/progress/${downloadId}`);

                eventSource.onmessage = function (event) {
                    const progress = JSON.parse(event.data);

                    if (progress.error) {
                        showToast('Error: ' + progress.error);
                        eventSource.close();
                        hideProgressBar();
                        return;
                    }

                    if (progress.keepalive) {
                        return;
                    }

                    updateProgress(progress.percent, progress.status);

                    if (progress.done) {
                        eventSource.close();
                        setTimeout(() => {
                            hideProgressBar();
                            if (progress.status === 'completed') {
                                showToast('Download completed! Optimizing...');
                                setTimeout(() => location.reload(), 2000);
                            } else {
                                showToast('Download failed: ' + progress.status);
                            }
                        }, 1000);
                    }
                };

                eventSource.onerror = function () {
                    console.error('EventSource error');
                    eventSource.close();
                    setTimeout(() => {
                        hideProgressBar();
                        showToast('Connection lost. Please refresh.');
                    }, 1000);
                };

            } else {
                showToast('Download failed: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred.');
        });
}

// File Menu Functions
function showFileMenu(event, fileId, sourceType, filename) {
    event.stopPropagation();
    currentFileId = fileId;
    currentFileType = sourceType;
    currentFileName = filename;

    const fileMenu = document.getElementById('file-menu');
    if (fileMenu) {
        fileMenu.classList.remove('hidden');
    }
}

function closeFileMenu() {
    const fileMenu = document.getElementById('file-menu');
    if (fileMenu) {
        fileMenu.classList.add('hidden');
    }
}

function deleteCurrentFile() {
    if (!currentFileId) return;

    fetch(`/delete/${currentFileId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            closeFileMenu();
            if (data.status === 'success') {
                showToast('File deleted');
                setTimeout(() => location.reload(), 500);
            } else {
                showToast('Delete failed: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred.');
        });
}

// Open File with Resume Support
function openFile(fileId, sourceType, filename, optimizedUrl) {
    console.log('🎬 Opening file:', { fileId, sourceType, filename, optimizedUrl });

    const videoExtensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv'];
    const filenameLower = filename.toLowerCase();
    const isVideo = videoExtensions.some(ext => filenameLower.endsWith(ext));

    if (isVideo) {
        const videoModal = document.getElementById('video-modal');
        const videoPlayer = document.getElementById('video-player');
        const videoTitle = document.getElementById('video-title');

        if (!videoModal || !videoPlayer || !videoTitle) {
            console.error('❌ Video elements not found!');
            return;
        }

        currentFileId = fileId;
        videoTitle.textContent = filename;

        // URL cleanup: Handle Python 'None' string or nulls
        if (optimizedUrl === 'None' || optimizedUrl === 'null' || !optimizedUrl) {
            optimizedUrl = null;
        }

        // Use optimized video if available, otherwise fallback to standard file serving
        const videoUrl = optimizedUrl || `/files/${sourceType}/${encodeURIComponent(filename)}`;
        console.log('🎥 Video URL:', videoUrl);

        videoPlayer.src = videoUrl;
        videoPlayer.preload = 'auto';

        videoModal.classList.remove('hidden');

        // Load saved watch position
        fetch(`/get-watch-position/${fileId}`)
            .then(response => response.json())
            .then(data => {
                console.log('📍 Watch position data:', data);

                if (data.status === 'success' && data.position > 5) {
                    videoPlayer.currentTime = data.position;
                    showToast(`Resuming from ${formatTime(data.position)}`);
                }

                // Auto-play
                videoPlayer.load();
                const playPromise = videoPlayer.play();

                if (playPromise !== undefined) {
                    playPromise.then(() => {
                        console.log('✅ Playing from', data.position);
                        // Trigger fullscreen for ALL devices as requested
                        requestFullscreen(videoPlayer);
                    }).catch(error => {
                        console.error('❌ Play error:', error);
                        showToast('Tap to play');
                    });
                }
            })
            .catch(error => {
                console.error('❌ Error fetching watch position:', error);
                videoPlayer.load();
                videoPlayer.play();
            });

    } else {
        window.open(`/files/${sourceType}/${encodeURIComponent(filename)}`, '_blank');
    }
}

// Setup Video Player with Watch History
function setupVideoPlayer() {
    const videoPlayer = document.getElementById('video-player');
    if (!videoPlayer) return;

    // Update watch position every 5 seconds
    videoPlayer.addEventListener('playing', function () {
        if (watchPositionInterval) {
            clearInterval(watchPositionInterval);
        }

        watchPositionInterval = setInterval(() => {
            if (currentFileId && !videoPlayer.paused) {
                updateWatchPosition();
            }
        }, 5000); // Update every 5 seconds
    });

    // Save on pause
    videoPlayer.addEventListener('pause', function () {
        if (currentFileId) {
            updateWatchPosition();
        }
    });

    // Save on seek
    videoPlayer.addEventListener('seeked', function () {
        if (currentFileId) {
            updateWatchPosition();
        }
    });

    // Save on end
    videoPlayer.addEventListener('ended', function () {
        if (currentFileId) {
            updateWatchPosition();
        }
        showToast('Video ended');
    });

    // Fullscreen handlers
    videoPlayer.addEventListener('fullscreenchange', function () {
        if (!document.fullscreenElement) {
            closeVideoModal();
        }
    });

    videoPlayer.addEventListener('webkitfullscreenchange', function () {
        if (!document.webkitFullscreenElement) {
            closeVideoModal();
        }
    });
}

// Update watch position on server
function updateWatchPosition() {
    const videoPlayer = document.getElementById('video-player');
    if (!videoPlayer || !currentFileId) return;

    const position = videoPlayer.currentTime;
    const duration = videoPlayer.duration;

    if (isNaN(position) || isNaN(duration)) return;

    fetch('/update-watch-position', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            file_id: currentFileId,
            position: position,
            duration: duration
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Watch position updated:', position);
            }
        })
        .catch(error => {
            console.error('Error updating watch position:', error);
        });
}

// Close Video Modal
function closeVideoModal() {
    const videoModal = document.getElementById('video-modal');
    const videoPlayer = document.getElementById('video-player');

    if (!videoModal || !videoPlayer) return;

    // Save final position
    if (currentFileId) {
        updateWatchPosition();
    }

    // Clear interval
    if (watchPositionInterval) {
        clearInterval(watchPositionInterval);
        watchPositionInterval = null;
    }

    // Exit fullscreen
    if (document.fullscreenElement || document.webkitFullscreenElement) {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }

    videoPlayer.pause();
    videoPlayer.src = "";
    videoModal.classList.add('hidden');
    currentFileId = null;
}

// Helper: Format time (seconds to MM:SS)
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Helper: Mobile device detection
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Helper: Request fullscreen
function requestFullscreen(element) {
    try {
        if (element.requestFullscreen) {
            element.requestFullscreen().catch(err => console.log('Fullscreen error:', err));
        } else if (element.webkitEnterFullscreen) {
            element.webkitEnterFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }
    } catch (err) {
        console.log('Fullscreen not supported:', err);
    }
}

// Toast Notification
function showToast(message) {
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 72px;
        left: 50%;
        transform: translateX(-50%);
        background: #323232;
        color: white;
        padding: 14px 24px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 400;
        animation: fadeInUp 0.3s ease-out;
        max-width: 90%;
        text-align: center;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// CSS animations
if (!document.querySelector('#toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}
