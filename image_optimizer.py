

import os
import io
from PIL import Image, ImageOps
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageOptimizer:
    def __init__(self):
        self.max_width = 1200
        self.max_height = 800
        self.quality = 80
        self.format = 'JPEG'
        
    def optimize_image(self, image_data, filename):
        try:
            image = Image.open(image_data)
            
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_width, original_height = image.size
            logger.info(f"Original image size: {original_width}x{original_height}")
            
            if original_width <= self.max_width and original_height <= self.max_height:
                logger.info(f"Image already small enough, skipping resize")
                image = ImageOps.exif_transpose(image)
            else:
                ratio = min(self.max_width / original_width, self.max_height / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                image = image.resize((new_width, new_height), Image.Resampling.BILINEAR)
                logger.info(f"Resized to: {new_width}x{new_height}")
                
                image = ImageOps.exif_transpose(image)
            
            output = io.BytesIO()
            
            if filename.lower().endswith('.png'):
                self.format = 'PNG'
                image.save(output, format='PNG', optimize=False)
            elif filename.lower().endswith('.webp'):
                self.format = 'WEBP'
                image.save(output, format='WEBP', quality=self.quality)
            else:
                self.format = 'JPEG'
                image.save(output, format='JPEG', quality=self.quality, optimize=False)
            
            output.seek(0)
            
            original_size = len(image_data.read()) if hasattr(image_data, 'read') else 0
            optimized_size = len(output.getvalue())
            compression_ratio = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
            
            logger.info(f"Optimized {filename}: {original_size/1024/1024:.1f}MB -> {optimized_size/1024/1024:.1f}MB ({compression_ratio:.1f}% reduction)")
            
            return output
            
        except Exception as e:
            logger.error(f"Error optimizing image {filename}: {str(e)}")
            if hasattr(image_data, 'seek'):
                image_data.seek(0)
            return image_data
    
    def get_optimized_filename(self, original_filename):
        name, ext = os.path.splitext(original_filename)
        
        if self.format == 'PNG':
            return f"{name}_optimized.png"
        elif self.format == 'WEBP':
            return f"{name}_optimized.webp"
        else:
            return f"{name}_optimized.jpg" 