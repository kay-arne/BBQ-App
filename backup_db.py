#!/usr/bin/env python3
"""
Database backup script for BBQ app
Creates timestamped backups of the SQLite database
"""

import os
import shutil
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_database(db_path='bbq.db', backup_dir='backups'):
    """Create a backup of the database"""
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"Created backup directory: {backup_dir}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Generate timestamp for backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"bbq_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Create backup using SQLite backup API
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        # Use SQLite backup API for proper backup
        source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        # Verify backup
        backup_size = os.path.getsize(backup_path)
        original_size = os.path.getsize(db_path)
        
        if backup_size > 0 and backup_size == original_size:
            logger.info(f"Database backup created successfully: {backup_path}")
            logger.info(f"Backup size: {backup_size} bytes")
            return True
        else:
            logger.error("Backup verification failed - size mismatch")
            os.remove(backup_path)
            return False
            
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        return False

def cleanup_old_backups(backup_dir='backups', keep_days=30):
    """Remove backup files older than specified days"""
    
    if not os.path.exists(backup_dir):
        return
    
    current_time = datetime.now().timestamp()
    cutoff_time = current_time - (keep_days * 24 * 60 * 60)
    
    removed_count = 0
    for filename in os.listdir(backup_dir):
        if filename.startswith('bbq_backup_') and filename.endswith('.db'):
            file_path = os.path.join(backup_dir, filename)
            file_time = os.path.getmtime(file_path)
            
            if file_time < cutoff_time:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {filename}")
                except Exception as e:
                    logger.error(f"Error removing old backup {filename}: {e}")
    
    if removed_count > 0:
        logger.info(f"Cleaned up {removed_count} old backup files")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    db_path = os.getenv('DATABASE_PATH', 'bbq.db')
    
    logger.info("Starting database backup...")
    
    if backup_database(db_path):
        logger.info("Backup completed successfully")
        cleanup_old_backups()
    else:
        logger.error("Backup failed")
        exit(1)


