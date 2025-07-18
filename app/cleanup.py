import os
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_temp_directories():
    """
    Deletes the contents of temporary directories used in the video creation workflow.
    """
    # Define the directories to clean
    temp_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'temp')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'downloaded_videos'))
    ]

    logger.info("Starting cleanup of temporary directories...")

    for directory in temp_dirs:
        if not os.path.isdir(directory):
            logger.warning(f"Directory not found, skipping: {directory}")
            continue

        logger.info(f"Cleaning directory: {directory}")
        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    logger.info(f"Deleted file: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.info(f"Deleted directory: {item_path}")
            except Exception as e:
                logger.error(f'Failed to delete {item_path}. Reason: {e}')

    logger.info("Cleanup of temporary directories completed.")

if __name__ == '__main__':
    # This allows the script to be run directly for testing or manual cleanup
    cleanup_temp_directories()
