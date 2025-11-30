#!/usr/bin/env python3
"""
Example client for the Pharo Reviewer Agent API

Demonstrates proper usage including retry logic for 503 responses
"""
import requests
import time
from typing import Dict, Any


def refactor_with_retry(
    class_name: str,
    method_name: str,
    base_url: str = "http://localhost:8000",
    max_retries: int = 5
) -> Dict[str, Any]:
    """
    Refactor a Pharo method with exponential backoff for 503 responses.

    Since the API can only process one request at a time (due to the single
    MCP stdio connection), this function implements retry logic with
    exponential backoff.

    Args:
        class_name: Name of the Pharo class
        method_name: Name of the method to refactor
        base_url: Base URL of the API
        max_retries: Maximum number of retry attempts

    Returns:
        Response JSON from the API

    Raises:
        requests.HTTPError: For non-503 HTTP errors
        Exception: If max retries exceeded
    """
    url = f"{base_url}/api/v1/refactor"
    payload = {
        "refactor_request": {
            "class_name": class_name,
            "method_name": method_name
        }
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=300)  # 5 min timeout

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 503:
                # Agent is busy, retry with exponential backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
                print(f"⏳ Agent busy, retrying in {wait_time}s... "
                      f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

            else:
                # Other HTTP errors (4xx, 5xx) - don't retry
                response.raise_for_status()

        except requests.Timeout:
            print(f"⏱️  Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

        except requests.RequestException as e:
            print(f"❌ Request error: {e}")
            raise

    raise Exception(f"Failed after {max_retries} retries - agent may be overloaded")


def check_health(base_url: str = "http://localhost:8000") -> bool:
    """
    Check if the API is healthy.

    Args:
        base_url: Base URL of the API

    Returns:
        True if healthy, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy - {data['app_name']} v{data['version']}")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ API health check failed: {e}")
        return False


def main():
    """Main entry point"""
    print("🤖 Pharo Reviewer Agent API Client\n")

    # Check API health first
    if not check_health():
        print("\n⚠️  API is not available. Make sure the server is running:")
        print("    python run.py --dev")
        return

    # Example refactoring request
    print("\n" + "=" * 60)
    print("Requesting refactoring...")
    print("=" * 60 + "\n")

    class_name = input("Enter class name (e.g., 'Calculator'): ").strip()
    method_name = input("Enter method name (e.g., 'sum:with:'): ").strip()

    if not class_name or not method_name:
        print("❌ Both class name and method name are required.")
        return

    print(f"\n🔄 Refactoring {class_name}>>{method_name}...\n")

    try:
        result = refactor_with_retry(class_name, method_name)

        if result.get("success"):
            print("\n" + "=" * 60)
            print("✅ REFACTORING SUCCESSFUL")
            print("=" * 60)

            # Display results
            agent_result = result.get("result", {})

            if "code_review" in agent_result:
                print("\n📋 Code Review:")
                print(agent_result["code_review"])

            if "refactored_code" in agent_result:
                print("\n📝 Refactored Code:")
                print(agent_result["refactored_code"])

            if "release_status" in agent_result:
                print(f"\n🚀 Release Status: {agent_result['release_status']}")

        else:
            print(f"\n❌ Refactoring failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
