"""
Database configuration for FastAPI with SQLAlchemy
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, MetaData, inspect, Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
import asyncpg
from databases import Database

# Database configurations
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://sexto_andar_user:sexto_andar_pass@localhost:5432/sexto_andar_db"
)

# For async connections
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# SQLAlchemy configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Avoids connection issues in containers
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"  # Log SQL queries if SQL_DEBUG=true
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Base for models
Base = declarative_base()

# Base model class with common fields
class BaseModel(Base):
    """
    Base class for all models.
    Includes common fields like ID, timestamps, etc.
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()")
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()")
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()")
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

# Metadata configuration
metadata = MetaData()

# Database instance for async operations
database = Database(DATABASE_URL)

# Dependency to get database session
def get_db():
    """
    Dependency that provides a database session.
    Use with Depends() in FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to get database session for scripts
def get_sync_db():
    """
    Get synchronous database session for use in scripts.
    Remember to close the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Synchronous function to initialize database for scripts
def initialize_database_sync():
    """Initialize database synchronously for scripts"""
    try:
        logging.info("🔄 Initializing database (sync)...")
        
        # Test connection with a simple query
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            logging.info("✅ Database connection successful")
        except Exception as e:
            logging.error(f"❌ Database connection failed: {e}")
            return False
        finally:
            session.close()
        
        # Validate models
        if not validate_models():
            return False
            
        # Create tables if they don't exist
        if not create_tables():
            return False
            
        logging.info("✅ Database initialization completed successfully (sync)")
        return True
        
    except Exception as e:
        logging.error(f"❌ Database initialization failed (sync): {e}")
        return False

# Async function to connect to database
async def connect_db():
    """Connect to database (use on application startup)"""
    await database.connect()
    logging.info("✅ Connected to PostgreSQL database")

# Async function to disconnect from database
async def disconnect_db():
    """Disconnect from database (use on application shutdown)"""
    await database.disconnect()
    logging.info("📴 Disconnected from PostgreSQL database")

# Function to create all tables
def create_tables():
    """Create all tables and apply migrations for existing structures"""
    try:
        # Apply all necessary migrations first
        apply_migrations()
        
        # Then create/update tables
        Base.metadata.create_all(bind=engine)
        logging.info("🗄️  Tables created/verified successfully")
        return True
    except SQLAlchemyError as e:
        logging.error(f"❌ Error creating tables: {e}")
        return False

def apply_migrations():
    """Apply database migrations for schema changes"""
    try:
        logging.info("🔄 Applying database migrations...")
        
        session = SessionLocal()
        inspector = inspect(engine)
        
        try:
            # 1. Update enums
            update_enums(session)
            
            # 2. Check and add new columns
            update_table_columns(session, inspector)
            
            # 3. Update constraints and indexes
            update_constraints_and_indexes(session, inspector)
            
            session.commit()
            logging.info("✅ All migrations applied successfully")
            
        except Exception as e:
            session.rollback()
            logging.error(f"❌ Migration failed: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"❌ Error applying migrations: {e}")
        # Don't fail completely, let create_all try
        pass

def update_enums(session):
    """Update enum types in PostgreSQL database"""
    try:
        logging.info("📝 Updating enum types...")
        
        # Update RoleEnum to include 'admin' if not exists
        try:
            session.execute(text("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'ADMIN';"))
            logging.info("✅ RoleEnum updated with 'ADMIN' value")
        except Exception as e:
            # Value might already exist
            logging.info(f"ℹ️  RoleEnum: {e}")
            
        # Add other enum updates here as needed
        # Example: session.execute(text("ALTER TYPE otherenum ADD VALUE IF NOT EXISTS 'newvalue';"))
            
    except Exception as e:
        logging.error(f"❌ Error updating enums: {e}")
        raise

def update_table_columns(session, inspector):
    """Update table columns to match current models"""
    logger = logging.getLogger(__name__)
    try:
        logger.info("� Checking for table column updates...")
        
        # Update accounts table - make phoneNumber nullable
        result = session.execute(text("""
            SELECT column_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'phoneNumber'
        """)).fetchone()
        
        if result and result[1] == 'NO':  # is_nullable = 'NO'
            logger.info("📝 Making phoneNumber column nullable in accounts table...")
            session.execute(text('ALTER TABLE accounts ALTER COLUMN "phoneNumber" DROP NOT NULL'))
            session.commit()
            logger.info("✅ phoneNumber column is now nullable")
        
        logger.info("✅ Table columns updated successfully")
    except Exception as e:
        logger.error(f"❌ Error updating table columns: {e}")
        raise

def update_constraints_and_indexes(session, inspector):
    """Update constraints and indexes"""
    try:
        logging.info("🔗 Checking constraints and indexes...")
        
        # Get all tables from our models
        model_tables = Base.metadata.tables
        
        for table_name, table in model_tables.items():
            if table_name in inspector.get_table_names():
                
                # Check indexes
                db_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
                
                for index in table.indexes:
                    if index.name not in db_indexes:
                        logging.info(f"🏷️  Creating missing index: {index.name}")
                        try:
                            session.execute(text(str(index.create(bind=engine))))
                        except Exception as e:
                            logging.warning(f"⚠️  Could not create index {index.name}: {e}")
                
                # Check foreign keys
                db_foreign_keys = {fk['name'] for fk in inspector.get_foreign_keys(table_name)}
                
                for constraint in table.foreign_key_constraints:
                    if constraint.name not in db_foreign_keys:
                        logging.info(f"🔗 Creating missing foreign key: {constraint.name}")
                        try:
                            session.execute(text(str(constraint.create(bind=engine))))
                        except Exception as e:
                            logging.warning(f"⚠️  Could not create foreign key {constraint.name}: {e}")
                            
    except Exception as e:
        logging.error(f"❌ Error updating constraints and indexes: {e}")
        # Don't fail for constraint issues
        pass

# Function to validate models
def validate_models():
    """Validate all SQLAlchemy models"""
    try:
        # Import all models to ensure they're registered with Base
        # NOTE: account model is in sexto-andar-auth service, not here
        from ..models import property, address, visit, proposal
        
        # Get inspector to check database structure
        inspector = inspect(engine)
        
        # Validate that all models are properly configured
        for table in Base.metadata.tables.values():
            logging.info(f"✅ Model validated: {table.name}")
            
        # Check if we can create a session
        session = SessionLocal()
        session.close()
        
        logging.info("✅ All models validated successfully")
        return True
        
    except Exception as e:
        logging.error(f"❌ Model validation error: {e}")
        return False

# Function to initialize database
async def initialize_database():
    """Initialize database: connect, validate models, create tables"""
    try:
        logging.info("🔄 Initializing database...")
        
        # Test connection first
        if not await check_database_connection():
            return False
            
        # Validate models
        if not validate_models():
            return False
            
        # Create tables if they don't exist
        if not create_tables():
            return False
            
        logging.info("✅ Database initialization completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
        return False

# Function to check connection
async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        if not database.is_connected:
            await database.connect()
        await database.fetch_val("SELECT 1")
        return True
    except Exception as e:
        logging.error(f"❌ Database connection error: {e}")
        return False
