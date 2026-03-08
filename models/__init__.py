"""Models package for ChatVLMLLM."""

from models.base_model import BaseModel
from models.got_ocr import GOTOCRModel
from models.qwen_vl import QwenVLModel
from models.qwen3_vl import Qwen3VLModel
from models.dots_ocr_final import DotsOCRFinalModel
# DotsOCRModel is a backward-compatible alias; both are re-exported for external consumers
from models.dots_ocr import DotsOCRModel
from models.phi3_vision import Phi3VisionModel
from models.got_ocr_variants import GOTOCRUCASModel, GOTOCRHFModel
from models.model_loader import ModelLoader

__all__ = [
    "BaseModel",
    "GOTOCRModel",
    "QwenVLModel",
    "Qwen3VLModel",
    "DotsOCRFinalModel",
    "DotsOCRModel",
    "Phi3VisionModel",
    "GOTOCRUCASModel",
    "GOTOCRHFModel",
    "ModelLoader",
]