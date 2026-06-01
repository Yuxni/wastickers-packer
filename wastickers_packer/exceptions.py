class StickerError(Exception):
    """Base for all whatsappsticker errors."""

class ImageConversionError(StickerError):
    """A sticker or tray image could not be processed."""

class InputError(StickerError):
    """Input directory or files are invalid."""
