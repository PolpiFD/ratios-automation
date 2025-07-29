"""
Service de conversion d'images vers PDF
Respecte les principes Clean Code et SOLID
"""

import io
import logging
from pathlib import Path
from typing import Tuple, Optional
from enum import Enum

import img2pdf
from PIL import Image


class ImageFormat(Enum):
    """Formats d'images supportés"""
    JPEG = "jpeg"
    JPG = "jpg" 
    PNG = "png"
    HEIC = "heic"
    HEIF = "heif"


class ConversionError(Exception):
    """Exception personnalisée pour les erreurs de conversion"""
    pass


class ImageProcessor:
    """Responsabilité unique : traitement et normalisation des images"""
    
    @staticmethod
    def _fix_image_orientation(image: Image.Image) -> Image.Image:
        """Corrige l'orientation de l'image basée sur les métadonnées EXIF"""
        try:
            exif = image.getexif()
            if exif is not None:
                # Utilisation du code EXIF standard pour l'orientation (274)
                orientation = exif.get(274)  # 274 = ORIENTATION EXIF tag
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, TypeError):
            # Pas de données EXIF ou orientation non trouvée
            pass
        return image
    
    @staticmethod
    def _normalize_image_for_pdf(image: Image.Image) -> Image.Image:
        """Normalise l'image pour une conversion PDF optimale"""
        # Conversion en RGB si nécessaire (PDF ne supporte pas RGBA/P)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc pour les images avec transparence
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def process_image_bytes(self, image_bytes: bytes) -> bytes:
        """
        Traite et normalise une image à partir de bytes
        
        Args:
            image_bytes: Bytes de l'image source
            
        Returns:
            bytes: Image normalisée en bytes
            
        Raises:
            ConversionError: Erreur lors du traitement
        """
        try:
            # Tentative de support HEIF/HEIC si disponible
            heic_supported = False
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                heic_supported = True
            except ImportError:
                logging.debug("pillow-heif non installé, HEIC/HEIF non supporté")
            
            try:
                with Image.open(io.BytesIO(image_bytes)) as image:
                    # Vérifier si c'est HEIC sans support
                    if image.format in ('HEIF', 'HEIC') and not heic_supported:
                        raise ConversionError("Format HEIC non supporté. Installez pillow-heif pour le support HEIC.")
                    
                    # Corriger l'orientation
                    image = self._fix_image_orientation(image)
                    
                    # Normaliser pour PDF
                    image = self._normalize_image_for_pdf(image)
                    
                    # Convertir en bytes
                    output_buffer = io.BytesIO()
                    image.save(output_buffer, format='JPEG', quality=95, optimize=True)
                    return output_buffer.getvalue()
                    
            except Exception as e:
                # Distinguer les erreurs de format des autres erreurs
                if "cannot identify image file" in str(e).lower():
                    raise ConversionError("Format d'image non reconnu ou corrompu")
                raise ConversionError(f"Erreur lors du traitement de l'image: {str(e)}")
                
        except Exception as e:
            raise ConversionError(f"Erreur lors du traitement de l'image: {str(e)}")


class PDFGenerator:
    """Responsabilité unique : génération de PDF à partir d'images"""
    
    def convert_image_to_pdf(self, processed_image_bytes: bytes) -> bytes:
        """
        Convertit une image traitée en PDF
        
        Args:
            processed_image_bytes: Image normalisée en bytes
            
        Returns:
            bytes: PDF généré
            
        Raises:
            ConversionError: Erreur lors de la conversion
        """
        try:
            # img2pdf pour une conversion optimisée sans perte
            pdf_bytes = img2pdf.convert(processed_image_bytes)
            return pdf_bytes
            
        except Exception as e:
            raise ConversionError(f"Erreur lors de la conversion PDF: {str(e)}")


class FileNameGenerator:
    """Responsabilité unique : génération des noms de fichiers"""
    
    @staticmethod
    def generate_pdf_name(original_filename: str) -> str:
        """
        Génère un nom de fichier PDF à partir du nom original
        
        Args:
            original_filename: Nom de fichier original
            
        Returns:
            str: Nom de fichier PDF
        """
        original_path = Path(original_filename)
        return f"{original_path.stem}.pdf"


class FormatValidator:
    """Responsabilité unique : validation des formats de fichiers"""
    
    @staticmethod
    def is_supported_image_format(filename: str) -> bool:
        """
        Vérifie si le format de fichier est supporté
        
        Args:
            filename: Nom du fichier
            
        Returns:
            bool: True si supporté
        """
        if not filename:
            return False
            
        suffix = Path(filename).suffix.lower().lstrip('.')
        
        try:
            ImageFormat(suffix)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_image_format(filename: str) -> Optional[ImageFormat]:
        """
        Retourne le format de l'image
        
        Args:
            filename: Nom du fichier
            
        Returns:
            ImageFormat ou None si non supporté
        """
        if not FormatValidator.is_supported_image_format(filename):
            return None
            
        suffix = Path(filename).suffix.lower().lstrip('.')
        return ImageFormat(suffix)


class PDFConverterService:
    """
    Service principal de conversion d'images vers PDF
    Orchestre les différents composants selon le principe Single Responsibility
    """
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.pdf_generator = PDFGenerator()
        self.filename_generator = FileNameGenerator()
        self.format_validator = FormatValidator()
    
    async def convert_image_to_pdf(
        self, 
        image_bytes: bytes, 
        original_filename: str
    ) -> Tuple[bytes, str]:
        """
        Convertit une image en PDF
        
        Args:
            image_bytes: Contenu de l'image en bytes
            original_filename: Nom de fichier original
            
        Returns:
            Tuple[bytes, str]: (PDF bytes, nom PDF)
            
        Raises:
            ConversionError: Erreur lors de la conversion
        """
        if not image_bytes:
            raise ConversionError("Données d'image vides")
        
        if not self.format_validator.is_supported_image_format(original_filename):
            raise ConversionError(f"Format non supporté: {original_filename}")
        
        try:
            logging.info(f"Début conversion PDF: {original_filename}")
            
            # 1. Traitement et normalisation de l'image
            processed_image_bytes = self.image_processor.process_image_bytes(image_bytes)
            
            # 2. Conversion en PDF
            pdf_bytes = self.pdf_generator.convert_image_to_pdf(processed_image_bytes)
            
            # 3. Génération du nom de fichier PDF
            pdf_filename = self.filename_generator.generate_pdf_name(original_filename)
            
            logging.info(f"Conversion réussie: {original_filename} → {pdf_filename}")
            
            return pdf_bytes, pdf_filename
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"Erreur inattendue lors de la conversion: {str(e)}")


# Instance globale du service (Singleton pattern)
pdf_converter_service = PDFConverterService()