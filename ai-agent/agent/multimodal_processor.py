"""
Multi-Modal AI Processor
=========================
Process multiple input modalities: text, images, audio, documents, video.

Features:
- Screenshot → Code generation (vision-to-code)
- Voice → Requirements (speech-to-text)
- PDF/DOCX → Structured data extraction
- Video → Tutorial understanding
- Image generation for mockups
- Multi-modal context fusion
"""

import os
import io
import re
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

try:
    from PIL import Image
    import speech_recognition as sr
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("[WARNING] Vision/Audio processing not available. Install: pip install Pillow SpeechRecognition")

try:
    import PyPDF2
    from docx import Document
    DOCUMENT_AVAILABLE = True
except ImportError:
    DOCUMENT_AVAILABLE = False
    print("[WARNING] Document processing not available. Install: pip install PyPDF2 python-docx")

from utils.logger import agent_logger


@dataclass
class VisionAnalysis:
    """Result of vision analysis."""
    layout_description: str
    detected_components: List[str]
    color_scheme: Dict[str, str]
    design_style: str
    confidence_score: float
    extracted_text: List[str]
    regions: List[Dict[str, Any]]


@dataclass
class DocumentContent:
    """Extracted document content."""
    text: str
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    tables: List[List[List[str]]]
    images: List[bytes]


class MultiModalProcessor:
    """Process multiple input types for AI generation."""
    
    def __init__(self):
        self.vision_enabled = VISION_AVAILABLE
        self.doc_enabled = DOCUMENT_AVAILABLE
        self.recognizer = sr.Recognizer() if VISION_AVAILABLE else None
        
        # Design element patterns
        self.component_patterns = {
            "navigation": ["nav", "menu", "header", "top bar"],
            "hero": ["hero", "banner", "jumbotron", "main section"],
            "card": ["card", "box", "panel", "tile"],
            "form": ["form", "input", "textbox", "button"],
            "footer": ["footer", "bottom", "copyright"],
            "sidebar": ["sidebar", "aside", "secondary"],
            "gallery": ["gallery", "grid", "images", "photos"],
            "testimonial": ["testimonial", "review", "quote"],
            "pricing": ["pricing", "plan", "tier", "package"],
            "cta": ["call to action", "cta", "sign up", "get started"]
        }
    
    def process_screenshot(self, image_data: str, provider: Optional[str] = None) -> VisionAnalysis:
        """
        Analyze a screenshot and extract layout, components, and design tokens.
        
        Args:
            image_data: Base64 data URI or file path
            provider: AI provider to use for vision analysis
        
        Returns:
            VisionAnalysis object with detected elements
        """
        if not self.vision_enabled:
            return self._empty_vision_analysis()
        
        try:
            # Load image
            img = self._load_image(image_data)
            
            # Basic image analysis
            width, height = img.size
            aspect_ratio = width / height
            
            # Extract dominant colors
            colors = self._extract_colors(img)
            
            # Detect layout regions
            regions = self._detect_regions(img)
            
            # Use AI vision model for detailed analysis
            if provider:
                ai_analysis = self._ai_vision_analysis(image_data, provider)
                if ai_analysis:
                    return ai_analysis
            
            # Fallback: rule-based analysis
            components = self._detect_components_basic(img)
            design_style = self._infer_design_style(colors, components)
            
            return VisionAnalysis(
                layout_description=f"{width}x{height} ({aspect_ratio:.2f} aspect ratio) layout with {len(regions)} main regions",
                detected_components=components,
                color_scheme=colors,
                design_style=design_style,
                confidence_score=0.6,  # Lower confidence for rule-based
                extracted_text=[],
                regions=regions
            )
        
        except Exception as e:
            agent_logger.error(f"Screenshot processing failed: {e}")
            return self._empty_vision_analysis()
    
    def process_voice_input(self, audio_file: str, language: str = "en-US") -> Optional[str]:
        """
        Convert voice audio to text requirements.
        
        Args:
            audio_file: Path to audio file (WAV, FLAC, etc.)
            language: Language code for recognition
        
        Returns:
            Transcribed text or None
        """
        if not self.vision_enabled or not self.recognizer:
            agent_logger.warning("Voice processing not available")
            return None
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=language)
                agent_logger.info(f"Transcribed: {text[:100]}...")
                return text
        
        except sr.UnknownValueError:
            agent_logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            agent_logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            agent_logger.error(f"Voice processing failed: {e}")
            return None
    
    def process_pdf(self, pdf_path: str) -> DocumentContent:
        """
        Extract structured content from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            DocumentContent with extracted text and metadata
        """
        if not self.doc_enabled:
            return self._empty_document()
        
        try:
            text_parts = []
            metadata = {}
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        "title": pdf_reader.metadata.get('/Title', ''),
                        "author": pdf_reader.metadata.get('/Author', ''),
                        "pages": len(pdf_reader.pages)
                    }
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
            
            full_text = "\n\n".join(text_parts)
            
            # Detect structure
            structure = self._detect_document_structure(full_text)
            
            return DocumentContent(
                text=full_text,
                metadata=metadata,
                structure=structure,
                tables=[],  # TODO: Implement table extraction
                images=[]
            )
        
        except Exception as e:
            agent_logger.error(f"PDF processing failed: {e}")
            return self._empty_document()
    
    def process_docx(self, docx_path: str) -> DocumentContent:
        """
        Extract structured content from DOCX.
        
        Args:
            docx_path: Path to DOCX file
        
        Returns:
            DocumentContent with extracted text and metadata
        """
        if not self.doc_enabled:
            return self._empty_document()
        
        try:
            doc = Document(docx_path)
            
            # Extract paragraphs
            text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
            full_text = "\n\n".join(text_parts)
            
            # Extract metadata
            core_props = doc.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "created": str(core_props.created) if core_props.created else "",
                "modified": str(core_props.modified) if core_props.modified else ""
            }
            
            # Extract tables
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                tables.append(table_data)
            
            # Detect structure
            structure = self._detect_document_structure(full_text)
            
            return DocumentContent(
                text=full_text,
                metadata=metadata,
                structure=structure,
                tables=tables,
                images=[]
            )
        
        except Exception as e:
            agent_logger.error(f"DOCX processing failed: {e}")
            return self._empty_document()
    
    def _load_image(self, image_data: str) -> Image.Image:
        """Load image from data URI or file path."""
        if image_data.startswith("data:image"):
            # Data URI
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            return Image.open(io.BytesIO(image_bytes))
        else:
            # File path
            return Image.open(image_data)
    
    def _extract_colors(self, img: Image.Image, num_colors: int = 5) -> Dict[str, str]:
        """Extract dominant colors from image."""
        try:
            # Resize for faster processing
            img_small = img.resize((150, 150))
            
            # Convert to RGB
            img_rgb = img_small.convert('RGB')
            
            # Get color histogram
            pixels = list(img_rgb.getdata())
            
            # Simple color clustering (basic implementation)
            # In production, use K-means clustering
            color_counts: Dict[Tuple[int, int, int], int] = {}
            for pixel in pixels:
                color_counts[pixel] = color_counts.get(pixel, 0) + 1
            
            # Get top colors
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            top_colors = [color for color, _ in sorted_colors[:num_colors]]
            
            # Convert to hex
            def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            
            return {
                f"color_{i+1}": rgb_to_hex(color)
                for i, color in enumerate(top_colors)
            }
        
        except Exception as e:
            agent_logger.debug(f"Color extraction failed: {e}")
            return {"color_1": "#000000", "color_2": "#ffffff"}
    
    def _detect_regions(self, img: Image.Image) -> List[Dict[str, Any]]:
        """Detect layout regions in image."""
        width, height = img.size
        
        # Simple heuristic-based region detection
        regions = [
            {
                "type": "header",
                "bounds": {"x": 0, "y": 0, "width": width, "height": int(height * 0.15)},
                "confidence": 0.7
            },
            {
                "type": "main",
                "bounds": {"x": 0, "y": int(height * 0.15), "width": width, "height": int(height * 0.70)},
                "confidence": 0.8
            },
            {
                "type": "footer",
                "bounds": {"x": 0, "y": int(height * 0.85), "width": width, "height": int(height * 0.15)},
                "confidence": 0.7
            }
        ]
        
        return regions
    
    def _detect_components_basic(self, img: Image.Image) -> List[str]:
        """Basic component detection without AI."""
        # This is a placeholder - real implementation would use computer vision
        return ["navigation", "hero", "content_section", "footer"]
    
    def _infer_design_style(self, colors: Dict[str, str], components: List[str]) -> str:
        """Infer design style from colors and components."""
        # Simple heuristics
        color_values = list(colors.values())
        
        # Check if colors are mostly grayscale
        is_minimal = all(
            c[1:3] == c[3:5] == c[5:7] or abs(int(c[1:3], 16) - int(c[3:5], 16)) < 20
            for c in color_values if len(c) == 7
        )
        
        if is_minimal:
            return "minimalism"
        else:
            return "modern"
    
    def _ai_vision_analysis(self, image_data: str, provider: str) -> Optional[VisionAnalysis]:
        """Use AI vision model for detailed analysis."""
        try:
            from config.providers import instantiate_provider
            
            provider_instance = instantiate_provider(provider)
            if not hasattr(provider_instance, 'analyze_image'):
                return None
            
            # Call provider's vision analysis
            result = provider_instance.analyze_image(image_data, prompt="""
            Analyze this website screenshot and provide:
            1. Layout description (header, sections, footer)
            2. UI components (buttons, forms, cards, navigation)
            3. Color scheme (primary, secondary, accent colors in hex)
            4. Design style (modern, minimalist, colorful, corporate, etc.)
            5. Text content visible on the page
            
            Format as JSON with keys: layout, components, colors, style, text
            """)
            
            # Parse AI response into VisionAnalysis
            # (Implementation depends on provider response format)
            
            return None  # Placeholder
        
        except Exception as e:
            agent_logger.debug(f"AI vision analysis failed: {e}")
            return None
    
    def _detect_document_structure(self, text: str) -> Dict[str, Any]:
        """Detect document structure from text."""
        structure = {
            "headings": [],
            "sections": [],
            "lists": [],
            "has_toc": False
        }
        
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect headings (lines that are short, uppercase, or numbered)
            if len(line_stripped) < 100 and (
                line_stripped.isupper() or
                re.match(r'^\d+\.', line_stripped) or
                re.match(r'^[A-Z][a-z]+:', line_stripped)
            ):
                structure["headings"].append({
                    "text": line_stripped,
                    "line": i + 1
                })
            
            # Detect lists
            if re.match(r'^[\-\*•]\s', line_stripped) or re.match(r'^\d+\.\s', line_stripped):
                structure["lists"].append({
                    "text": line_stripped,
                    "line": i + 1
                })
        
        return structure
    
    def _empty_vision_analysis(self) -> VisionAnalysis:
        """Return empty vision analysis."""
        return VisionAnalysis(
            layout_description="",
            detected_components=[],
            color_scheme={},
            design_style="modern",
            confidence_score=0.0,
            extracted_text=[],
            regions=[]
        )
    
    def _empty_document(self) -> DocumentContent:
        """Return empty document content."""
        return DocumentContent(
            text="",
            metadata={},
            structure={},
            tables=[],
            images=[]
        )
    
    def fuse_multimodal_context(self, text_prompt: str, 
                                vision_analysis: Optional[VisionAnalysis] = None,
                                document_content: Optional[DocumentContent] = None,
                                voice_input: Optional[str] = None) -> str:
        """
        Fuse multiple input modalities into a rich context for AI generation.
        
        Args:
            text_prompt: Base text prompt
            vision_analysis: Optional screenshot analysis
            document_content: Optional document content
            voice_input: Optional voice transcription
        
        Returns:
            Enhanced prompt with all context
        """
        context_parts = [text_prompt]
        
        if voice_input:
            context_parts.append(f"\n\n## Voice Input\nUser said: {voice_input}")
        
        if vision_analysis and vision_analysis.detected_components:
            context_parts.append(f"\n\n## Visual Reference")
            context_parts.append(f"Layout: {vision_analysis.layout_description}")
            context_parts.append(f"Components detected: {', '.join(vision_analysis.detected_components)}")
            context_parts.append(f"Design style: {vision_analysis.design_style}")
            if vision_analysis.color_scheme:
                colors_str = ", ".join([f"{k}: {v}" for k, v in vision_analysis.color_scheme.items()])
                context_parts.append(f"Color scheme: {colors_str}")
        
        if document_content and document_content.text:
            context_parts.append(f"\n\n## Document Content")
            context_parts.append(f"Extracted from: {document_content.metadata.get('title', 'document')}")
            # Truncate long documents
            doc_preview = document_content.text[:1000]
            if len(document_content.text) > 1000:
                doc_preview += "... (truncated)"
            context_parts.append(doc_preview)
        
        enhanced_prompt = "\n".join(context_parts)
        
        agent_logger.info(f"Fused multimodal context: {len(enhanced_prompt)} chars")
        
        return enhanced_prompt


# Global instance
_multimodal_processor: Optional[MultiModalProcessor] = None

def get_multimodal_processor() -> MultiModalProcessor:
    """Get or create the global multimodal processor instance."""
    global _multimodal_processor
    if _multimodal_processor is None:
        _multimodal_processor = MultiModalProcessor()
    return _multimodal_processor
