#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify Chatwoot API connection.

This script tests the connection to the Chatwoot API using the correct authentication format.
"""

import os
import sys
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_chatwoot_connection():
    """Test the connection to the Chatwoot API."""
    # Load environment variables
    load_dotenv()

    # Get Chatwoot API credentials from environment variables
    chatwoot_base_url = os.getenv("CHATWOOT_BASE_URL")
    chatwoot_api_key = os.getenv("CHATWOOT_API_KEY")
    account_id = os.getenv("CHATWOOT_ACCOUNT_ID", "1")

    if not chatwoot_base_url or not chatwoot_api_key:
        logger.error("Missing Chatwoot API credentials in .env file")
        return False

    # Ensure the base URL doesn't end with a slash
    chatwoot_base_url = chatwoot_base_url.rstrip('/')

    # Test with api_access_token header (correct format)
    logger.info(f"Testing connection to {chatwoot_base_url} with api_access_token header")
    headers_correct = {
        'api_access_token': chatwoot_api_key,
        'Content-Type': 'application/json'
    }

    # Test with Authorization header (incorrect format)
    logger.info(f"Testing connection to {chatwoot_base_url} with Authorization header")
    headers_incorrect = {
        'Authorization': f'Bearer {chatwoot_api_key}',
        'Content-Type': 'application/json'
    }

    # Endpoint to test
    # Remove /api/v1 from the endpoint if it's already in the base_url
    if chatwoot_base_url.endswith('/api/v1'):
        endpoint = f"/accounts/{account_id}/inboxes"
    else:
        endpoint = f"/api/v1/accounts/{account_id}/inboxes"
    url = f"{chatwoot_base_url}{endpoint}"

    # Test with correct headers
    try:
        logger.info(f"Making GET request to: {url}")
        logger.info(f"Headers: {headers_correct}")

        response = requests.get(url, headers=headers_correct)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ Connection successful with api_access_token header!")
            logger.info(f"Response: {response.json()}")
            correct_works = True
        else:
            logger.error(f"❌ Connection failed with api_access_token header: {response.status_code}")
            logger.error(f"Response: {response.text}")
            correct_works = False
    except Exception as e:
        logger.error(f"❌ Error connecting with api_access_token header: {str(e)}")
        correct_works = False

    # Test with incorrect headers
    try:
        logger.info(f"Making GET request to: {url}")
        logger.info(f"Headers: {headers_incorrect}")

        response = requests.get(url, headers=headers_incorrect)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ Connection successful with Authorization header!")
            logger.info(f"Response: {response.json()}")
            incorrect_works = True
        else:
            logger.error(f"❌ Connection failed with Authorization header: {response.status_code}")
            logger.error(f"Response: {response.text}")
            incorrect_works = False
    except Exception as e:
        logger.error(f"❌ Error connecting with Authorization header: {str(e)}")
        incorrect_works = False

    # Summary
    logger.info("\n=== Connection Test Summary ===")
    logger.info(f"api_access_token header: {'✅ Works' if correct_works else '❌ Fails'}")
    logger.info(f"Authorization header: {'✅ Works' if incorrect_works else '❌ Fails'}")

    return correct_works

if __name__ == "__main__":
    success = test_chatwoot_connection()
    sys.exit(0 if success else 1)
