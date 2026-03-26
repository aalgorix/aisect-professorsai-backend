"""
Celery Tasks for PDF Processing
Handles long-running PDF uploads and course generation in background workers
"""

import logging
import os
import sys
import tempfile
from typing import List, Dict, Any
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app
import config
from services.document_service import DocumentService

# Initialize document service
document_service = DocumentService()

@celery_app.task(
    bind=True,
    name='tasks.pdf_processing.process_pdf_and_generate_course',
    queue='pdf_processing',
    max_retries=3,
    default_retry_delay=60
)
def process_pdf_and_generate_course(
    self,
    job_id: str,
    pdf_files_data: List[Dict[str, Any]],
    course_title: str = None,
    country: str = None
) -> Dict[str, Any]:
    """
    Process PDF files and generate course content.
    
    This task runs in a separate worker pod and can scale horizontally.
    
    Args:
        job_id: Unique job identifier
        pdf_files_data: List of dicts with 'filename' and 'content' (base64 encoded)
        course_title: Optional course title
        country: Country where course is offered (e.g., 'India', 'USA')
        
    Returns:
        Dict with course data or error information
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={
                'status': 'processing',
                'progress': 10,
                'message': 'Starting PDF processing...'
            }
        )
        
        logging.info(f"[Job {job_id}] Processing {len(pdf_files_data)} PDF files")
        
        # Files are already saved to shared volume by the API
        # Process PDFs using existing document service
        # Use process_pdf_files_from_paths which accepts file path dicts
        result = document_service.process_pdf_files_from_paths(
            pdf_files_data,
            course_title,
            country=country,
            progress_callback=lambda progress, msg: self.update_state(
                state='STARTED',
                meta={
                    'status': 'processing',
                    'progress': progress,
                    'message': msg
                }
            )
        )
            
        # Success
        logging.info(f"[Job {job_id}] Course generated successfully: {result.get('course_id')}")
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'result': {
                'course_id': result.get('course_id'),
                'course_title': result.get('course_title'),
                'modules': len(result.get('modules', []))
            }
        }
    
    except Exception as exc:
        error_msg = str(exc)
        error_trace = traceback.format_exc()
        logging.error(f"[Job {job_id}] Task failed: {error_msg}")
        logging.error(error_trace)
        
        # Only retry on transient errors (connection issues, timeouts)
        # Don't retry on permanent errors (invalid PDF, course generation failure)
        transient_errors = (ConnectionError, TimeoutError, OSError)
        is_transient = isinstance(exc, transient_errors) or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower()
        
        if is_transient and self.request.retries < self.max_retries:
            logging.info(f"[Job {job_id}] Transient error detected, retrying ({self.request.retries + 1}/{self.max_retries})...")
            raise self.retry(exc=exc, countdown=60)
        
        # Permanent failure - don't retry
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': error_msg
        }


@celery_app.task(
    bind=True,
    name='tasks.pdf_processing.batch_process_pdfs',
    queue='pdf_processing'
)
def batch_process_pdfs(
    self,
    job_ids: List[str],
    pdf_files_batch: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process multiple PDF uploads in batch.
    Useful for bulk uploads by teachers.
    
    Args:
        job_ids: List of job identifiers
        pdf_files_batch: List of PDF file data
        
    Returns:
        List of results
    """
    results = []
    
    for job_id, pdf_data in zip(job_ids, pdf_files_batch):
        try:
            result = process_pdf_and_generate_course.apply_async(
                args=[job_id, pdf_data['files'], pdf_data.get('course_title')],
                priority=pdf_data.get('priority', 5)
            )
            results.append({
                'job_id': job_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return results


@celery_app.task(
    name='tasks.pdf_processing.cleanup_old_jobs',
    queue='pdf_processing'
)
def cleanup_old_jobs():
    """
    Periodic task to clean up old job records.
    Runs daily to remove completed jobs older than 7 days.
    """
    from datetime import datetime, timedelta
    
    try:
        # TODO: Implement cleanup logic when database is enabled
        # Delete jobs older than 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        logging.info(f"Cleaning up jobs older than {cutoff_date}")
        
        # This will be implemented with database
        pass
        
    except Exception as e:
        logging.error(f"Cleanup task failed: {e}")
