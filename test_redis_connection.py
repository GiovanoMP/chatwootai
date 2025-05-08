#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify Redis connection.

This script tests the connection to Redis using the configuration from the .env file.
"""

import os
import sys
import logging
import redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test the connection to Redis."""
    # Load environment variables
    load_dotenv()
    
    # Get Redis configuration from environment variables
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_password = os.getenv("REDIS_PASSWORD", "")
    
    logger.info("Testing Redis connection...")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Redis Host: {redis_host}")
    logger.info(f"Redis Port: {redis_port}")
    logger.info(f"Redis DB: {redis_db}")
    logger.info(f"Redis Password: {'*****' if redis_password else 'None'}")
    
    # Try connecting using Redis URL first
    if redis_url:
        try:
            logger.info(f"Connecting to Redis using URL: {redis_url}")
            r = redis.from_url(redis_url)
            r.ping()
            logger.info("✅ Connection successful using Redis URL!")
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to Redis using URL: {str(e)}")
    
    # Try connecting using individual parameters
    try:
        logger.info(f"Connecting to Redis using host/port: {redis_host}:{redis_port}")
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password if redis_password else None,
            socket_timeout=5
        )
        r.ping()
        logger.info("✅ Connection successful using host/port!")
        return True
    except Exception as e:
        logger.error(f"❌ Error connecting to Redis using host/port: {str(e)}")
    
    logger.error("❌ All Redis connection attempts failed")
    return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
