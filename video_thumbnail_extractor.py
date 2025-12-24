

import os
import io
import requests
from PIL import Image
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoThumbnailExtractor:
    def __init__(self):
        self.timeout = 30
        
    def extract_thumbnail_from_url(self, video_url: str) -> io.BytesIO:
        try:
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                return self._extract_youtube_thumbnail(video_url)
            
            elif 'vimeo.com' in video_url:
                return self._extract_vimeo_thumbnail(video_url)
            
            else:
                return self._create_generic_video_thumbnail(video_url)
                
        except Exception as e:
            logger.error(f"Error extracting thumbnail from {video_url}: {str(e)}")
            return self._create_generic_video_thumbnail(video_url)
    
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