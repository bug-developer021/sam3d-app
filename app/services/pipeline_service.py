import sys
import os
import logging

# Add root to sys.path to allow importing pipeline.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from pipeline import Forma3DPipeline
except ImportError:
    # Fallback for when running from root
    from pipeline import Forma3DPipeline

from app.core.config import settings

logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self):
        self._pipeline = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            logger.info("Initializing Forma3D Pipeline...")
            self._pipeline = Forma3DPipeline()
        return self._pipeline
    
    def process_job(self, job_id: str, image_path: str):
        """
        Runs the pipeline for a given job.
        This is intended to be run in a background task.
        """
        logger.info(f"Starting job {job_id} for image {image_path}")
        
        # Define output base path (pipeline adds extensions)
        output_base = os.path.join(settings.OUTPUT_DIR, job_id)
        
        try:
            result = self.pipeline.run(image_path, output_base)
            logger.info(f"Job {job_id} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {}

    def process_job_multiview(self, job_id: str, image_paths: list):
        """
        Runs the pipeline for a multi-view job.
        """
        logger.info(f"Starting multi-view job {job_id} for {len(image_paths)} images")
        
        output_base = os.path.join(settings.OUTPUT_DIR, job_id)
        
        try:
            result = self.pipeline.run_multiview(image_paths, output_base)
            logger.info(f"Job {job_id} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {}

pipeline_service = PipelineService()
