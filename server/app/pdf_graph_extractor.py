import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import base64
import io
from PIL import Image
import os

logger = logging.getLogger(__name__)

class PDFGraphExtractor:
    """Extract graphs and figures from PDF textbooks"""
    
    def __init__(self, pdf_directory: str = None):
        if pdf_directory is None:
            # Use the actual data directory
            self.pdf_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        else:
            self.pdf_directory = pdf_directory
            
        # Map of available PDFs
        self.pdf_files = {
            "2021": "Princeton Review AP Economics Micro & Macro Prep, 2021_ 4 -- The Princeton The Princeton Review -- 2021 edition, New York, NY _, 2020 -- Random House -- 9780525569503 -- 25db4b22ab8f29b8f9b7cbf6f6f9b5f0 -- Anna's Archive.pdf",
            "2020": "Cracking the AP Economics Micro & Macro Exams, 2020 Edition_ -- Princeton Review Staff; The Princeton Review -- Penguin Random House LLC, [N_p_], 2019 -- 9780525568209 -- c5f779b7d623e240e101d0def160fc70 -- Anna's Archive.pdf",
            "2019": "Cracking the AP Economics Macroeconomics and Microeconomics -- Princeton Review Staff; The Princeton Review -- Penguin Random House LLC, [N_p_], 2019 -- 9780525568209 -- 228895d8e820e49cb5db93e8eadda1eb -- Anna's Archive.pdf",
            "2018": "Cracking the AP Economics Macro & Micro Exams, 2018 Edition_ -- Review, Princeton(Contributor) -- Penguin Random House LLC, New York, NY, 2017 -- 9781524710057 -- 1cf122260738a27d81d8cc62e9069d80 -- Anna's Archive.pdf"
        }
        
    async def extract_graphs_from_chapter(self, subject: str, unit: int, chapter: str) -> List[Dict[str, Any]]:
        """
        Extract graphs from a specific chapter in a PDF textbook
        
        Args:
            subject: Subject name (e.g., "micro", "macro")
            unit: Unit number
            chapter: Chapter identifier (e.g., "1.1", "1.2")
            
        Returns:
            List of graph data dictionaries with image, title, and description
        """
        try:
            # Use the most recent PDF (2021 edition)
            pdf_filename = self.pdf_files.get("2021")
            if not pdf_filename:
                logger.warning("No PDF file configured")
                return []
                
            pdf_path = os.path.join(self.pdf_directory, pdf_filename)
            
            if not os.path.exists(pdf_path):
                logger.warning(f"PDF not found: {pdf_path}")
                return []
            
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # You'll need to implement logic to find the right pages for the chapter
            # This is a simplified example
            graphs = []
            
            # Map chapters to page ranges (you'll need to build this mapping)
            chapter_pages = self._get_chapter_pages(subject, unit, chapter)
            
            for page_num in chapter_pages:
                if page_num >= len(doc):
                    continue
                    
                page = doc[page_num]
                
                # Extract images from the page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    # Get the image
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    img_pil = Image.open(io.BytesIO(img_data))
                    
                    # Check if this looks like a graph (basic heuristic)
                    if self._is_likely_graph(img_pil):
                        # Convert to base64
                        buffered = io.BytesIO()
                        img_pil.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Try to extract caption/title from nearby text
                        title, description = self._extract_graph_caption(page, img)
                        
                        graphs.append({
                            "type": "extracted",
                            "image": img_base64,
                            "title": title or f"Figure {img_index + 1}",
                            "description": description or "Graph extracted from textbook",
                            "source_page": page_num + 1
                        })
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    
            doc.close()
            return graphs
            
        except Exception as e:
            logger.error(f"Error extracting graphs from PDF: {e}")
            return []
    
    def _get_chapter_pages(self, subject: str, unit: int, chapter: str) -> List[int]:
        """
        Get page numbers for a specific chapter
        This needs to be implemented based on your PDF structure
        """
        # This is a placeholder - you'll need to implement actual page mapping
        # Could use PDF bookmarks/outline or maintain a separate index
        chapter_page_map = {
            "micro": {
                "1.1": range(10, 15),  # Pages 11-15
                "1.2": range(15, 20),  # Pages 16-20
                # Add more mappings
            }
        }
        
        if subject in chapter_page_map and chapter in chapter_page_map[subject]:
            return list(chapter_page_map[subject][chapter])
        
        return []
    
    def _is_likely_graph(self, image: Image.Image) -> bool:
        """
        Simple heuristic to determine if an image is likely a graph
        """
        # Check aspect ratio (graphs are often square-ish or landscape)
        width, height = image.size
        aspect_ratio = width / height
        
        # Check if it's too small (likely an icon or decoration)
        if width < 200 or height < 200:
            return False
        
        # Check if it's too thin (likely a line or separator)
        if aspect_ratio > 5 or aspect_ratio < 0.2:
            return False
        
        # You could add more sophisticated checks here:
        # - Check for axis lines
        # - Check for typical graph colors
        # - Use ML model to classify images
        
        return True
    
    def _extract_graph_caption(self, page: fitz.Page, img_info: tuple) -> tuple[Optional[str], Optional[str]]:
        """
        Try to extract caption text near the image
        """
        try:
            # Get text blocks near the image
            blocks = page.get_text("blocks")
            
            # Simple approach: look for "Figure X.X" or "Graph X.X" patterns
            for block in blocks:
                text = block[4]
                if "Figure" in text or "Graph" in text or "Exhibit" in text:
                    lines = text.strip().split('\n')
                    title = lines[0] if lines else None
                    description = ' '.join(lines[1:]) if len(lines) > 1 else None
                    return title, description
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error extracting caption: {e}")
            return None, None

# Global instance
pdf_graph_extractor = PDFGraphExtractor()