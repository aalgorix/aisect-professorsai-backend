"""
Async Document Service - Wraps synchronous PDF processing in background tasks
"""

import asyncio
import logging
from typing import List
from fastapi import UploadFile
from concurrent.futures import ThreadPoolExecutor
import traceback

from models.job_status import job_tracker, JobStatus
from services.document_service import DocumentService

# Thread pool for running blocking operations
executor = ThreadPoolExecutor(max_workers=3)  # Allow up to 3 concurrent PDF processing jobs

class AsyncDocumentService:
    """
    Asynchronous wrapper for DocumentService.
    Runs blocking PDF processing in background threads.
    """
    
    def __init__(self):
        self.document_service = DocumentService()
        # Expose database service from document service (if enabled)
        self.db_service = self.document_service.db_service
        if self.db_service:
            logging.info("AsyncDocumentService initialized with database support")
        else:
            logging.info("AsyncDocumentService initialized (JSON mode)")
    
    async def process_pdfs_async(
        self, 
        job_id: str,
        pdf_files_data: List[dict], 
        course_title: str = None
    ):
        """
        Process PDFs asynchronously in a background thread.
        Updates job status throughout the process.
        
        Args:
            job_id: Unique job identifier
            pdf_files_data: List of dicts with 'filename' and 'content' (bytes)
            course_title: Optional course title
        """
        temp_files = []
        try:
            import tempfile
            import os
            
            # Update status to processing
            job_tracker.update_status(job_id, JobStatus.PROCESSING, "Starting PDF processing...")
            job_tracker.update_progress(job_id, 5, "Preparing temporary files...")
            
            # Create temporary files for processing
            for file_data in pdf_files_data:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.write(file_data["content"])
                temp_file.close()
                temp_files.append({
                    "path": temp_file.name,
                    "filename": file_data["filename"]
                })
            
            # Run the blocking operation in a thread pool
            loop = asyncio.get_running_loop()
            
            # Progress callback for the document service
            def progress_callback(progress, message):
                job_tracker.update_progress(job_id, progress, message)
            
            # Execute in thread pool
            job_tracker.update_progress(job_id, 10, "Extracting text from PDFs...")
            
            course_data = await loop.run_in_executor(
                executor, 
                lambda: self.document_service.process_pdf_files_from_paths(
                    temp_files, 
                    course_title,
                    progress_callback=progress_callback
                )
            )
            
            # Mark as completed
            job_tracker.update_progress(job_id, 100, "Course generated successfully!")
            
            # Handle course_id
            course_id = course_data.get("course_id")
            job_tracker.set_result(job_id, {
                "course_id": str(course_id) if course_id else None,
                "course_title": course_data.get("course_title"),
                "modules_count": len(course_data.get("modules", []))
            })
            
            logging.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Job {job_id} failed: {error_msg}")
            logging.error(traceback.format_exc())
            job_tracker.set_error(job_id, error_msg)
        finally:
            # Cleanup temp files
            for tf in temp_files:
                try:
                    if os.path.exists(tf["path"]):
                        os.unlink(tf["path"])
                except:
                    pass

# Global instance
async_document_service = AsyncDocumentService()

# ============= ENHANCED VERSION WITH PROGRESS TRACKING =============
# TODO: For even better progress tracking, we can hook into the document service
# to update progress at each step (extracting, chunking, vectorizing, generating)
# This would require modifying document_service.py to accept a progress callback

"""
FUTURE ENHANCEMENT: Detailed Progress Tracking

To show detailed progress (e.g., "Extracting PDF 2/5", "Generating module 3/8"),
we can add a callback system:

# In document_service.py:
def process_uploaded_pdfs(self, pdf_files, course_title, progress_callback=None):
    if progress_callback:
        progress_callback(20, "Extracting text from PDFs...")
    
    for i, pdf_file in enumerate(pdf_files):
        # ... extract ...
        if progress_callback:
            progress = 20 + (i + 1) / len(pdf_files) * 20
            progress_callback(progress, f"Extracted {i+1}/{len(pdf_files)} PDFs")
    
    # ... and so on for each step

# Then in async_document_service.py:
def progress_callback(progress, message):
    job_tracker.update_progress(job_id, progress, message)

result = self.document_service.process_uploaded_pdfs(
    pdf_files, 
    course_title,
    progress_callback=progress_callback
)
"""
