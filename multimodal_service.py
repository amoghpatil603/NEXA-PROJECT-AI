from image_pipeline import ImagePipeline

class MultimodalService:
    def __init__(self):
        self.image_pipeline = ImagePipeline()

    def process_input(self, text=None, image_paths=None, audio_data=None):
        results = {"text": text, "images": []}
        
        if image_paths:
            for path in image_paths:
                processed = self.image_pipeline.process_image(path)
                results["images"].append(processed)
                
        # Handle audio data if needed
        return results
