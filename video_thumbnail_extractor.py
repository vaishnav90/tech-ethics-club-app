"""
Generate still thumbnails for video URLs (YouTube/Vimeo oEmbed or API patterns,
direct .mp4 etc. via OpenCV when installed, else placeholder).

Used when admins add gallery videos so the UI can show a preview tile.
"""

import os
import io
import requests
from PIL import Image
import logging
import tempfile


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoThumbnailExtractor:
    """Returns a PNG (BytesIO) suitable for upload as video thumbnail."""

    def __init__(self):
        self.timeout = 30
        
    def extract_thumbnail_from_url(self, video_url: str) -> io.BytesIO:
        """Dispatch by URL host/type; never raises — falls back to generic placeholder on error."""
        try:
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                return self._extract_youtube_thumbnail(video_url)
            
            elif 'vimeo.com' in video_url:
                return self._extract_vimeo_thumbnail(video_url)
            
            elif self._is_direct_video_file(video_url):
                # Try to extract frame from direct video file
                return self._extract_frame_from_video_file(video_url)
            
            else:
                return self._create_generic_video_thumbnail(video_url)
                
        except Exception as e:
            logger.error(f"Error extracting thumbnail from {video_url}: {str(e)}")
            return self._create_generic_video_thumbnail(video_url)
    
    def _is_direct_video_file(self, video_url: str) -> bool:
        """Check if URL points to a direct video file."""
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.flv', '.wmv']
        video_url_lower = video_url.lower()
        return any(video_url_lower.endswith(ext) for ext in video_extensions)
    
    def _extract_frame_from_video_file(self, video_url: str, time_seconds: float = 1.5) -> io.BytesIO:
        """Extract a frame from a video file at the specified time (default 1.5 seconds)."""
        try:
            # Try to use opencv (cv2) if available
            try:
                import cv2
                return self._extract_frame_with_opencv(video_url, time_seconds)
            except ImportError:
                logger.warning("OpenCV not available, trying alternative method")
                # Try alternative method with moviepy if available
                try:
                    from moviepy.editor import VideoFileClip
                    return self._extract_frame_with_moviepy(video_url, time_seconds)
                except ImportError:
                    logger.warning("MoviePy not available, falling back to generic thumbnail")
                    return self._create_generic_video_thumbnail(video_url)
        except Exception as e:
            logger.error(f"Error extracting frame from video file {video_url}: {str(e)}")
            return self._create_generic_video_thumbnail(video_url)
    
    def _extract_frame_with_opencv(self, video_url: str, time_seconds: float) -> io.BytesIO:
        """Extract frame using OpenCV."""
        import cv2
        import numpy as np
        
        temp_video_path = None
        try:
            # Download video to temporary file
            response = requests.get(video_url, timeout=self.timeout, stream=True)
            if response.status_code != 200:
                logger.warning(f"Failed to download video from {video_url}: HTTP {response.status_code}")
                return self._create_generic_video_thumbnail(video_url)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_video_path = temp_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_video_path)
            if not cap.isOpened():
                logger.warning(f"Failed to open video file: {temp_video_path}")
                return self._create_generic_video_thumbnail(video_url)
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = total_frames / fps if fps > 0 else 0
            
            if fps <= 0:
                fps = 30  # Default FPS if can't determine
            
            # Calculate frame number for desired time (use 1-2 seconds, default 1.5)
            # If video is shorter than desired time, use middle of video or frame 1
            if video_duration > 0 and video_duration < time_seconds:
                # Use middle of video if it's shorter than desired time
                target_time = video_duration / 2
            elif video_duration > 0:
                # Use desired time (1.5 seconds) but ensure it's within video duration
                target_time = min(time_seconds, video_duration - 0.1)
            else:
                # Fallback: use 1.5 seconds
                target_time = time_seconds
            
            frame_number = int(fps * target_time)
            # Ensure frame number is valid
            if frame_number >= total_frames and total_frames > 0:
                frame_number = max(0, total_frames - 1)
            elif frame_number < 0:
                frame_number = 0
            
            # Set video position to desired frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                logger.warning(f"Failed to read frame at {time_seconds}s from video")
                return self._create_generic_video_thumbnail(video_url)
            
            # Convert BGR to RGB (OpenCV uses BGR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Resize if too large (max 1920x1080)
            max_size = (1920, 1080)
            if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to BytesIO
            thumbnail_data = io.BytesIO()
            pil_image.save(thumbnail_data, format='JPEG', quality=85)
            thumbnail_data.seek(0)
            
            logger.info(f"Successfully extracted frame at {time_seconds}s from video file: {video_url}")
            return thumbnail_data
            
        except Exception as e:
            logger.error(f"Error extracting frame with OpenCV: {str(e)}")
            return self._create_generic_video_thumbnail(video_url)
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_video_path}: {e}")
    
    def _extract_frame_with_moviepy(self, video_url: str, time_seconds: float) -> io.BytesIO:
        """Extract frame using MoviePy (alternative method)."""
        from moviepy.editor import VideoFileClip
        
        temp_video_path = None
        try:
            # Download video to temporary file
            response = requests.get(video_url, timeout=self.timeout, stream=True)
            if response.status_code != 200:
                logger.warning(f"Failed to download video from {video_url}: HTTP {response.status_code}")
                return self._create_generic_video_thumbnail(video_url)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_video_path = temp_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
            
            # Open video with MoviePy
            clip = VideoFileClip(temp_video_path)
            
            # Get frame at specified time (clamp to video duration)
            frame_time = min(time_seconds, clip.duration - 0.1) if clip.duration > 0.1 else 0
            
            # Get frame as numpy array
            frame = clip.get_frame(frame_time)
            clip.close()
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame)
            
            # Resize if too large
            max_size = (1920, 1080)
            if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to BytesIO
            thumbnail_data = io.BytesIO()
            pil_image.save(thumbnail_data, format='JPEG', quality=85)
            thumbnail_data.seek(0)
            
            logger.info(f"Successfully extracted frame at {frame_time}s from video file using MoviePy: {video_url}")
            return thumbnail_data
            
        except Exception as e:
            logger.error(f"Error extracting frame with MoviePy: {str(e)}")
            return self._create_generic_video_thumbnail(video_url)
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_video_path}: {e}")
    
    def _extract_youtube_thumbnail(self, video_url: str) -> io.BytesIO:
        try:
            video_id = self._extract_youtube_id(video_url)
            if not video_id:
                return self._create_generic_video_thumbnail(video_url)
            
            thumbnail_urls = [
                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/default.jpg"
            ]
            
            for thumbnail_url in thumbnail_urls:
                try:
                    response = requests.get(thumbnail_url, timeout=self.timeout)
                    if response.status_code == 200:
                        thumbnail_data = io.BytesIO(response.content)
                        thumbnail_data.seek(0)
                        
                        try:
                            Image.open(thumbnail_data)
                            thumbnail_data.seek(0)
                            logger.info(f"Successfully extracted YouTube thumbnail from {video_url}")
                            return thumbnail_data
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Failed to get thumbnail from {thumbnail_url}: {e}")
                    continue
            
            return self._create_generic_video_thumbnail(video_url)
            
        except Exception as e:
            logger.error(f"Error extracting YouTube thumbnail: {e}")
            return self._create_generic_video_thumbnail(video_url)
    
    def _extract_vimeo_thumbnail(self, video_url: str) -> io.BytesIO:
        try:
            video_id = self._extract_vimeo_id(video_url)
            if not video_id:
                return self._create_generic_video_thumbnail(video_url)
            
            api_url = f"https://vimeo.com/api/v2/video/{video_id}.json"
            
            try:
                response = requests.get(api_url, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        thumbnail_url = data[0].get('thumbnail_large') or data[0].get('thumbnail_medium')
                        
                        if thumbnail_url:
                            thumb_response = requests.get(thumbnail_url, timeout=self.timeout)
                            if thumb_response.status_code == 200:
                                thumbnail_data = io.BytesIO(thumb_response.content)
                                thumbnail_data.seek(0)
                                
                                try:
                                    Image.open(thumbnail_data)
                                    thumbnail_data.seek(0)
                                    logger.info(f"Successfully extracted Vimeo thumbnail from {video_url}")
                                    return thumbnail_data
                                except Exception:
                                    pass
                                    
            except Exception as e:
                logger.warning(f"Failed to get Vimeo thumbnail: {e}")
            
            return self._create_generic_video_thumbnail(video_url)
            
        except Exception as e:
            logger.error(f"Error extracting Vimeo thumbnail: {e}")
            return self._create_generic_video_thumbnail(video_url)
    
    def _extract_youtube_id(self, video_url: str) -> str:
        import re
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_vimeo_id(self, video_url: str) -> str:
        import re
        
        patterns = [
            r'vimeo\.com\/(\d+)',
            r'vimeo\.com\/channels\/[^\/]+\/(\d+)',
            r'vimeo\.com\/groups\/[^\/]+\/videos\/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        return None
    
    def _create_generic_video_thumbnail(self, video_url: str) -> io.BytesIO:
        try:
            img = Image.new('RGB', (800, 450), color='#1a1a1a')
            
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            center_x, center_y = 400, 225
            radius = 60
            
            draw.ellipse([center_x - radius, center_y - radius, 
                         center_x + radius, center_y + radius], 
                        fill='rgba(255, 255, 255, 0.9)', outline='white', width=3)
            
            triangle_size = 30
            triangle_points = [
                (center_x - triangle_size//2, center_y - triangle_size),
                (center_x - triangle_size//2, center_y + triangle_size),
                (center_x + triangle_size, center_y)
            ]
            draw.polygon(triangle_points, fill='white')
            
            try:
                font = ImageFont.load_default()
                text = "VIDEO"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                text_x = center_x - text_width // 2
                text_y = center_y + radius + 20
                
                draw.text((text_x, text_y), text, fill='white', font=font)
            except Exception:
                pass
            
            thumbnail_data = io.BytesIO()
            img.save(thumbnail_data, format='JPEG', quality=85)
            thumbnail_data.seek(0)
            
            logger.info(f"Created generic video thumbnail for {video_url}")
            return thumbnail_data
            
        except Exception as e:
            logger.error(f"Error creating generic thumbnail: {e}")
            return None