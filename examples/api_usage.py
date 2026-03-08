"""ChatVLMLLM API usage examples."""

import requests
from pathlib import Path
import json

# API endpoint
API_URL = "http://localhost:8000"

def health_check():
    """Check API health and GPU status."""
    response = requests.get(f"{API_URL}/health", timeout=30)
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def list_models():
    """List available models."""
    response = requests.get(f"{API_URL}/models", timeout=30)
    print("\nAvailable Models:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def extract_text(image_path, model="qwen3_vl_2b", language=None):
    """Extract text from image using OCR."""
    with open(image_path, 'rb') as f:
        params = {'model': model}
        if language:
            params['language'] = language
        
        response = requests.post(
            f"{API_URL}/ocr",
            files={'file': f},
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nOCR Result ({model}):")
            print(f"Processing time: {result['processing_time']:.2f}s")
            print(f"Text: {result['text'][:200]}...")
            return result
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
            return None

def chat_with_image(image_path, prompt, model="qwen3_vl_2b", temperature=0.7):
    """Chat with VLM about an image."""
    with open(image_path, 'rb') as f:
        response = requests.post(
            f"{API_URL}/chat",
            files={'file': f},
            data={
                'prompt': prompt,
                'model': model,
                'temperature': temperature,
                'max_tokens': 512
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nChat Response ({model}):")
            print(f"Prompt: {prompt}")
            print(f"Response: {result['response']}")
            print(f"Processing time: {result['processing_time']:.2f}s")
            return result
        else:
            print(f"Error: {response.status_code}")
            return None

def batch_ocr(image_paths, model="qwen3_vl_2b"):
    """Process multiple images in batch."""
    file_handles = [open(path, 'rb') for path in image_paths]
    try:
        files = [('files', fh) for fh in file_handles]
        response = requests.post(
            f"{API_URL}/batch/ocr",
            files=files,
            params={'model': model},
            timeout=30
        )
    finally:
        for fh in file_handles:
            fh.close()
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nBatch OCR Results:")
        print(f"Total: {result['total']}")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
        
        for item in result['results']:
            if item['status'] == 'success':
                print(f"\n{item['filename']}:")
                print(f"  Time: {item['processing_time']:.2f}s")
                print(f"  Text: {item['text'][:100]}...")
            else:
                print(f"\n{item['filename']}: ERROR - {item['error']}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        return None

def compare_models(image_path, models=["qwen3_vl_2b", "dots_ocr"]):
    """Compare different models on the same image."""
    print(f"\nComparing models on {image_path}:")
    
    results = {}
    for model in models:
        result = extract_text(image_path, model=model)
        if result:
            results[model] = result
    
    print("\nComparison:")
    for model, result in results.items():
        print(f"\n{model}:")
        print(f"  Time: {result['processing_time']:.2f}s")
        print(f"  Text length: {len(result['text'])} chars")
    
    return results

def unload_model(model_name):
    """Unload model from memory."""
    response = requests.delete(f"{API_URL}/models/{model_name}", timeout=30)
    if response.status_code == 200:
        print(f"\nModel {model_name} unloaded successfully")
        return True
    else:
        print(f"Error unloading {model_name}: {response.status_code}")
        return False

if __name__ == "__main__":
    # Example usage
    
    # 1. Health check
    health = health_check()
    
    # 2. List models
    models = list_models()
    
    # Example image path (replace with your image)
    image_path = "test_image.jpg"
    
    if Path(image_path).exists():
        # 3. OCR
        ocr_result = extract_text(image_path, model="qwen3_vl_2b")
        
        # 4. OCR with language hint
        ocr_ru = extract_text(image_path, model="qwen3_vl_2b", language="Russian")
        
        # 5. Chat
        chat_result = chat_with_image(
            image_path,
            prompt="What is the main content of this document?",
            model="qwen3_vl_2b"
        )
        
        # 6. Compare models
        comparison = compare_models(
            image_path,
            models=["qwen3_vl_2b", "dots_ocr"]
        )
    else:
        print(f"\nImage not found: {image_path}")
        print("Please provide a test image to run examples.")
    
    # 7. Batch processing (if you have multiple images)
    # batch_images = ["doc1.jpg", "doc2.jpg", "doc3.jpg"]
    # if all(Path(p).exists() for p in batch_images):
    #     batch_result = batch_ocr(batch_images, model="qwen3_vl_2b")
    
    # 8. Unload model
    # unload_model("qwen3_vl_2b")