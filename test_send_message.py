#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to send a message to Chatwoot.

This script tests sending a message to a Chatwoot conversation using the correct authentication format.
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

def test_send_message(conversation_id=None):
    """Test sending a message to Chatwoot."""
    # Load environment variables
    load_dotenv()

    # Get Chatwoot API credentials from environment variables
    chatwoot_base_url = os.getenv("CHATWOOT_BASE_URL")
    chatwoot_api_key = os.getenv("CHATWOOT_API_KEY")
    account_id = os.getenv("CHATWOOT_ACCOUNT_ID", "1")

    if not chatwoot_base_url or not chatwoot_api_key:
        logger.error("Missing Chatwoot API credentials in .env file")
        return False

    # If no conversation_id is provided, ask for it
    if conversation_id is None:
        conversation_id = input("Enter conversation ID: ")

    # Ensure the base URL doesn't end with a slash
    chatwoot_base_url = chatwoot_base_url.rstrip('/')

    # Test with api_access_token header (correct format)
    logger.info(f"Testing sending message to {chatwoot_base_url} with api_access_token header")
    headers_correct = {
        'api_access_token': chatwoot_api_key,
        'Content-Type': 'application/json'
    }

    # Endpoint to test
    # Remove /api/v1 from the endpoint if it's already in the base_url
    if chatwoot_base_url.endswith('/api/v1'):
        endpoint = f"/accounts/{account_id}/conversations/{conversation_id}/messages"
    else:
        endpoint = f"/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    url = f"{chatwoot_base_url}{endpoint}"

    # Message data
    message_data = {
        'content': 'This is a test message from the API test script',
        'message_type': 'outgoing'
    }

    # Send message with correct headers
    try:
        logger.info(f"Making POST request to: {url}")
        logger.info(f"Headers: {headers_correct}")
        logger.info(f"Data: {message_data}")

        response = requests.post(url, headers=headers_correct, json=message_data)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ Message sent successfully with api_access_token header!")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"❌ Failed to send message with api_access_token header: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error sending message with api_access_token header: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if conversation_id was provided as command line argument
    conversation_id = sys.argv[1] if len(sys.argv) > 1 else None
    success = test_send_message(conversation_id)
    sys.exit(0 if success else 1)
