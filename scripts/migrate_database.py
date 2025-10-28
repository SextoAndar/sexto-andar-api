#!/usr/bin/env python3
"""
Database Migration Script
Real Estate Management API

This script handles database initialization and migrations.
Run this before starting the application for the first time or after model changes.
"""

import sys
import os
import logging
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.database.connection import (
    initialize_database_sync,
    create_tables,
    apply_migrations,
    validate_models,
    SessionLocal,
    engine
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_migrations():
    """Run all database migrations"""
    logger.info("=" * 60)
    logger.info("Starting Database Migration")
    logger.info("=" * 60)
    
    try:
        # Step 1: Validate models
        logger.info("Step 1: Validating models...")
        if not validate_models():
            logger.error("Model validation failed")
            return False
        logger.info("✅ Models validated successfully")
        
        # Step 2: Apply migrations
        logger.info("Step 2: Applying migrations...")
        apply_migrations()
        logger.info("✅ Migrations applied successfully")
        
        # Step 3: Create/update tables
        logger.info("Step 3: Creating/updating tables...")
        if not create_tables():
            logger.error("Table creation failed")
            return False
        logger.info("✅ Tables created/updated successfully")
        
        # Step 4: Verify connection
        logger.info("Step 4: Verifying database connection...")
        session = SessionLocal()
        try:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            logger.info("✅ Database connection verified")
        except Exception as e:
            logger.error(f"Database connection verification failed: {e}")
            return False
        finally:
            session.close()
            
        logger.info("=" * 60)
        logger.info("Database Migration Completed Successfully!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error("=" * 60)
        logger.error("Database Migration Failed!")
        logger.error("=" * 60)
        return False

def check_database_status():
    """Check current database status"""
    logger.info("Checking database status...")
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # List all tables
        tables = inspector.get_table_names()
        logger.info(f"Existing tables: {tables}")
        
        # Check if main tables exist
        # NOTE: 'accounts' table is NOT managed by this service - it's managed by sexto-andar-auth
        # This service only manages: properties, addresses, visits, proposals
        required_tables = ['properties', 'addresses', 'visits', 'proposals']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            return False
        else:
            logger.info("✅ All required tables exist")
            return True
            
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return False

def main():
    """Main function"""
    logger.info("Database Migration Tool")
    logger.info("Real Estate Management API")
    logger.info("")
    
    # Check if we should just check status
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_database_status()
        return
    
    # Check if we should force migrations
    force = len(sys.argv) > 1 and sys.argv[1] == "--force"
    
    if not force:
        # Check if migrations are needed
        if check_database_status():
            logger.info("Database appears to be up to date.")
            response = input("Do you want to run migrations anyway? (y/N): ")
            if response.lower() != 'y':
                logger.info("Migration cancelled.")
                return
    
    # Run migrations
    success = run_migrations()
    
    if success:
        logger.info("✅ Migration completed successfully!")
        logger.info("You can now start the application.")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed!")
        logger.error("Please check the logs and fix any issues before starting the application.")
        sys.exit(1)

if __name__ == "__main__":
    main()
