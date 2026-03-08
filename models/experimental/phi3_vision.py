"""Microsoft Phi-3.5 Vision model integration.

Official: https://huggingface.co/microsoft/Phi-3.5-vision-instruct
GitHub: https://github.com/microsoft/Phi-3CookBook

Phi-3.5 Vision is Microsoft's powerful vision-language model with:
- 4.2B parameters
- Strong multimodal capabilities
- Efficient inference
- Good performance on vision tasks
"""

from typing import Any, Dict, List, Optional, Union
from PIL import Image
import torch

from models.base_model import BaseModel
from utils.logger import logger


class Phi3VisionModel(BaseModel):
    """Microsoft Phi-3.5 Vision model."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.processor = None
        
        # Phi-3.5 Vision specific settings
        self.min_pixels = config.get('min_pixels', 256)
        self.max_pixels = config.get('max_pixels', 1280)
    
    def load_model(self) -> None:
        """Load Phi-3.5 Vision model."""
        try:
            from utils.logger import logger
            logger.info(f"Loading Phi-3.5 Vision from {self.model_path}")
            
            from transformers import AutoModelForCausalLM, AutoProcessor
            
            device = self._get_device()
            logger.info(f"Using device: {device}")
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Build loading kwargs
            load_kwargs = self._get_load_kwargs()
            
            # CRITICAL: Force eager attention to avoid Flash Attention issues
            load_kwargs['attn_implementation'] = "eager"
            
            # Remove invalid parameters that cause errors
            load_kwargs.pop('_attn_implementation', None)
            load_kwargs.pop('use_flash_attention_2', None)
            
            # Load model
            logger.info("Loading model weights...")
            
            # Try multiple approaches to disable Flash Attention
            try:
                # Method 1: Pre-load config and modify it
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(self.model_path, trust_remote_code=True)
                
                # Force disable Flash Attention in config - ALL possible attributes
                if hasattr(config, '_attn_implementation'):
                    config._attn_implementation = "eager"
                if hasattr(config, 'attn_implementation'):
                    config.attn_implementation = "eager"
                if hasattr(config, 'use_flash_attention_2'):
                    config.use_flash_attention_2 = False
                if hasattr(config, '_flash_attn_2_enabled'):
                    config._flash_attn_2_enabled = False
                if hasattr(config, 'flash_attention'):
                    config.flash_attention = False
                
                # Load with modified config
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    config=config,
                    **load_kwargs
                )
                
                # Move to device if not using device_map
                if not torch.cuda.is_available():
                    device = self._get_device()
                    self.model = self.model.to(device)
                    
            except Exception as e:
                logger.warning(f"Failed with config modification: {e}")
                
                # Method 2: Try with environment variable
                import os
                os.environ['TRANSFORMERS_ATTN_IMPLEMENTATION'] = 'eager'
                
                try:
                    # Remove device_map for CPU to avoid accelerate requirement
                    if not torch.cuda.is_available():
                        load_kwargs.pop('device_map', None)
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        **load_kwargs
                    )
                    
                    # Move to device manually
                    if not torch.cuda.is_available():
                        device = self._get_device()
                        self.model = self.model.to(device)
                        
                except Exception as e2:
                    logger.error(f"All loading methods failed: {e2}")
                    raise
            
            self.model.eval()
            logger.info("Phi-3.5 Vision loaded successfully")
            
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to load Phi-3.5 Vision: {e}")
            raise
    
    def process_image(
        self,
        image: Union[Image.Image, str],
        prompt: str = "Describe this image in detail.",
        **kwargs
    ) -> str:
        """Process image with Phi-3.5 Vision.
        
        Args:
            image: PIL Image or image path
            prompt: Text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Model response
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            logger.info("Processing image with Phi-3.5 Vision")
            
            # Ensure image is PIL Image
            if isinstance(image, str):
                image = Image.open(image)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Prepare messages in chat format
            messages = [
                {
                    "role": "user", 
                    "content": f"<|image_1|>\n{prompt}"
                }
            ]
            
            # Apply chat template
            try:
                prompt_text = self.processor.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
            except Exception as template_error:
                logger.warning(f"Chat template failed: {template_error}, using simple prompt")
                prompt_text = f"<|image_1|>\n{prompt}"
            
            # Process inputs with error handling
            try:
                inputs = self.processor(
                    prompt_text, 
                    [image], 
                    return_tensors="pt"
                )
                
                # Validate inputs
                if inputs is None:
                    raise ValueError("Processor returned None")
                
                # Handle BatchFeature object properly
                if hasattr(inputs, 'data'):
                    # BatchFeature object - extract data
                    inputs = inputs.data
                elif not isinstance(inputs, dict):
                    # Convert to dict if needed
                    if hasattr(inputs, 'keys') and hasattr(inputs, '__getitem__'):
                        inputs = {k: inputs[k] for k in inputs.keys()}
                    else:
                        raise ValueError(f"Expected dict or BatchFeature, got {type(inputs)}")
                
                if 'input_ids' not in inputs:
                    raise ValueError("input_ids not found in processor output")
                
            except Exception as process_error:
                logger.error(f"Processing failed: {process_error}")
                # Fallback: simple tokenization
                try:
                    text_inputs = self.processor.tokenizer(
                        prompt_text, 
                        return_tensors="pt", 
                        padding=True,
                        truncation=True
                    )
                    
                    # Simple image processing
                    import torchvision.transforms as transforms
                    
                    transform = transforms.Compose([
                        transforms.Resize((336, 336)),  # Phi-3.5 Vision input size
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                    ])
                    
                    pixel_values = transform(image).unsqueeze(0)
                    
                    inputs = {
                        'input_ids': text_inputs['input_ids'],
                        'attention_mask': text_inputs.get('attention_mask'),
                        'pixel_values': pixel_values
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback processing failed: {fallback_error}")
                    return f"[Phi-3.5 Vision processing error: {fallback_error}]"
            
            # Move to device
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) if torch.is_tensor(v) and v is not None else v for k, v in inputs.items()}
            
            # Generation parameters
            gen_kwargs = {
                'max_new_tokens': kwargs.get('max_new_tokens', 256),  # Reduced for stability
                'do_sample': kwargs.get('do_sample', False),
                'use_cache': False,  # Disable cache for stability
                'pad_token_id': self.processor.tokenizer.eos_token_id,
            }
            
            if kwargs.get('temperature'):
                gen_kwargs['temperature'] = kwargs['temperature']
                gen_kwargs['do_sample'] = True
            
            # Generate with robust error handling
            with torch.no_grad():
                try:
                    generated_ids = self.model.generate(**inputs, **gen_kwargs)
                    
                    if generated_ids is None:
                        raise ValueError("Generation returned None")
                    
                    # Decode only the new tokens
                    input_length = inputs['input_ids'].shape[1]
                    if generated_ids.shape[1] <= input_length:
                        return "[Phi-3.5 Vision: No new tokens generated]"
                    
                    new_tokens = generated_ids[0][input_length:]
                    output = self.processor.tokenizer.decode(new_tokens, skip_special_tokens=True)
                    
                    logger.info("Processing completed")
                    return output.strip() if output.strip() else "[Phi-3.5 Vision: Empty output]"
                    
                except Exception as gen_error:
                    logger.error(f"Generation failed: {gen_error}")
                    return f"[Phi-3.5 Vision generation error: {gen_error}]"
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"[Phi-3.5 Vision error: {e}]"
    
    def chat(
        self,
        image: Union[Image.Image, str],
        prompt: str,
        **kwargs
    ) -> str:
        """Chat with Phi-3.5 Vision about image.
        
        Args:
            image: PIL Image or path
            prompt: User question
            **kwargs: Generation parameters
            
        Returns:
            Model response
        """
        return self.process_image(image, prompt, **kwargs)
    
    def extract_text(
        self,
        image: Union[Image.Image, str],
        language: Optional[str] = None
    ) -> str:
        """Extract text from image using Phi-3.5 Vision.
        
        Args:
            image: PIL Image or path
            language: Optional language hint
            
        Returns:
            Extracted text
        """
        prompt = "Extract all text from this image. "
        if language:
            prompt += f"The text is in {language}. "
        prompt += "Maintain the original structure and formatting. Only return the extracted text."
        
        return self.process_image(image, prompt, max_new_tokens=1024)
    
    def analyze_document(
        self,
        image: Union[Image.Image, str],
        focus: str = "general"
    ) -> str:
        """Analyze document with specific focus.
        
        Args:
            image: PIL Image or path
            focus: Analysis focus (general, layout, content, tables)
            
        Returns:
            Analysis result
        """
        prompts = {
            "general": "Analyze this document and provide a comprehensive summary of its content and structure.",
            "layout": "Describe the layout, structure, and visual organization of this document.",
            "content": "Extract and summarize the main content and key information from this document.",
            "tables": "Identify and extract all tables from this document. Format them clearly."
        }
        
        prompt = prompts.get(focus, prompts["general"])
        return self.process_image(image, prompt, max_new_tokens=1024)
    
    def unload(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Phi-3.5 Vision unloaded")