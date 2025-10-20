

import os
import io
import requests
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GalleryPDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 0.75 * inch
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            alignment=TA_LEFT,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        self.creator_style = ParagraphStyle(
            'CreatorInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=colors.grey,
            fontName='Helvetica-Oblique'
        )
    
    def generate_gallery_item_pdf(self, gallery_item, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            title = Paragraph(gallery_item.get('title', 'Untitled Project'), self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            creators = gallery_item.get('creators', [])
            if creators:
                creator_text = "Created by: "
                creator_names = []
                for creator in creators:
                    name = creator.get('name', '')
                    school = creator.get('school', '')
                    if name:
                        if school:
                            creator_names.append(f"{name} ({school})")
                        else:
                            creator_names.append(name)
                
                if creator_names:
                    creator_text += ", ".join(creator_names)
                    creator_para = Paragraph(creator_text, self.creator_style)
                    story.append(creator_para)
                    story.append(Spacer(1, 15))
            
            description = gallery_item.get('description', '')
            if description:
                desc_para = Paragraph(description, self.body_style)
                story.append(desc_para)
                story.append(Spacer(1, 20))
            
            main_image_url = gallery_item.get('image_url')
            if main_image_url:
                if self._add_image_to_story(story, main_image_url, "Main Image"):
                    story.append(Spacer(1, 20))
            
            additional_images = gallery_item.get('additional_images', [])
            if additional_images:
                subtitle = Paragraph("Additional Images", self.subtitle_style)
                story.append(subtitle)
                story.append(Spacer(1, 10))
                
                for i, image_url in enumerate(additional_images):
                    if image_url:
                        caption = f"Image {i+1}"
                        if self._add_image_to_story(story, image_url, caption):
                            story.append(Spacer(1, 15))
            
            videos = gallery_item.get('videos', [])
            if videos:
                subtitle = Paragraph("Videos", self.subtitle_style)
                story.append(subtitle)
                story.append(Spacer(1, 10))
                
                for i, video in enumerate(videos):
                    video_title = video.get('title', f'Video {i+1}')
                    video_url = video.get('url', '')
                    video_thumbnail_url = video.get('thumbnail_url', '')
                    
                    video_title_para = Paragraph(f"<b>{video_title}</b>", self.body_style)
                    story.append(video_title_para)
                    
                    if video_url:
                        url_para = Paragraph(f"URL: {video_url}", self.creator_style)
                        story.append(url_para)
                    
                    if video_thumbnail_url:
                        if self._add_image_to_story(story, video_thumbnail_url, f"{video_title} Thumbnail"):
                            story.append(Spacer(1, 10))
                    else:
                        placeholder_para = Paragraph("<i>[Video thumbnail not available]</i>", self.creator_style)
                        story.append(placeholder_para)
                    
                    story.append(Spacer(1, 15))
            
            tags = gallery_item.get('tags', [])
            if tags:
                tags_text = f"Tags: {', '.join(tags)}"
                tags_para = Paragraph(tags_text, self.creator_style)
                story.append(tags_para)
                story.append(Spacer(1, 20))
            
            project_link = gallery_item.get('project_link')
            if project_link:
                link_text = f"Project Link: {project_link}"
                link_para = Paragraph(link_text, self.creator_style)
                story.append(link_para)
            
            doc.build(story)
            logger.info(f"Successfully generated PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return False
    
    def _add_image_to_story(self, story, image_url: str, caption: str = "") -> bool:
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Failed to download image from {image_url}")
                return False
            
            image_data = io.BytesIO(response.content)
            pil_image = Image.open(image_data)
            
            img_width, img_height = pil_image.size
            
            max_width = self.content_width - 0.5 * inch
            max_height = 4 * inch
            
            scale_factor = min(max_width / img_width, max_height / img_height)
            
            if scale_factor < 1:
                new_width = img_width * scale_factor
                new_height = img_height * scale_factor
            else:
                new_width = img_width
                new_height = img_height
            
            image_data.seek(0)
            
            rl_image = RLImage(image_data, width=new_width, height=new_height)
            
            story.append(rl_image)
            
            if caption:
                caption_para = Paragraph(f"<i>{caption}</i>", self.creator_style)
                story.append(caption_para)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding image to PDF: {str(e)}")
            return False
    
    def generate_gallery_pdf(self, gallery_items, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            main_title = Paragraph("Tech & Ethics Club - Project Gallery", self.title_style)
            story.append(main_title)
            story.append(Spacer(1, 30))
            
            for i, item in enumerate(gallery_items):
                if i > 0:
                    story.append(PageBreak())
                
                title = Paragraph(item.get('title', 'Untitled Project'), self.subtitle_style)
                story.append(title)
                story.append(Spacer(1, 15))
                
                creators = item.get('creators', [])
                if creators:
                    creator_text = "Created by: "
                    creator_names = []
                    for creator in creators:
                        name = creator.get('name', '')
                        school = creator.get('school', '')
                        if name:
                            if school:
                                creator_names.append(f"{name} ({school})")
                            else:
                                creator_names.append(name)
                    
                    if creator_names:
                        creator_text += ", ".join(creator_names)
                        creator_para = Paragraph(creator_text, self.creator_style)
                        story.append(creator_para)
                        story.append(Spacer(1, 10))
                
                description = item.get('description', '')
                if description:
                    desc_para = Paragraph(description, self.body_style)
                    story.append(desc_para)
                    story.append(Spacer(1, 15))
                
                main_image_url = item.get('image_url')
                if main_image_url:
                    if self._add_image_to_story(story, main_image_url, "Main Image"):
                        story.append(Spacer(1, 15))
                
                additional_images = item.get('additional_images', [])[:2]
                if additional_images:
                    for j, image_url in enumerate(additional_images):
                        if image_url:
                            caption = f"Additional Image {j+1}"
                            if self._add_image_to_story(story, image_url, caption):
                                story.append(Spacer(1, 10))
                
                videos = item.get('videos', [])
                if videos:
                    videos_text = f"Videos: {len(videos)} video(s) included"
                    videos_para = Paragraph(videos_text, self.creator_style)
                    story.append(videos_para)
            
            doc.build(story)
            logger.info(f"Successfully generated gallery PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating gallery PDF: {str(e)}")
            return False