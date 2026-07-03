import logging
import requests
import google.auth
import google.auth.transport.requests

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://asia-southeast1-aiplatform.googleapis.com/reasoningEngines/v1/projects/223456544745/locations/asia-southeast1/reasoningEngines/3898410835256541184/api"
CHAT_URL = f"{BASE_URL}/chat"

def get_auth_headers():
    """Fetch Google Cloud access token for authentication."""
    try:
        credentials, _ = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        return {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        logging.error(f"Failed to obtain auth token: {e}")
        return {}

def test_query(query_text, session_id="test-session-123"):
    headers = get_auth_headers()
    payload = {
        "user_id": "test-user-1",
        "session_id": session_id,
        "user_query": query_text
    }
    
    print(f"\nSending Query: '{query_text}' (session: {session_id})")
    try:
        response = requests.post(CHAT_URL, json=payload, headers=headers, timeout=60.0)
        print(f"HTTP Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Status:", data.get("status"))
            if data.get("status") == "interrupted":
                print("Interrupt ID:", data.get("interrupt_id"))
                print("Interrupt Message:", data.get("message"))
            else:
                print("Output Markdown:")
                print(data.get("output"))
                print("SQL Results Count:", len(data.get("sql_results", [])) if data.get("sql_results") else 0)
                print("Chart Type:", data.get("chart_type"))
            return data
        else:
            print("Error Details:", response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Unique session ID to run the full flow
    session_id = "test-session-full-flow-1"
    
    # 1. Trigger the query (expecting approval interrupt)
    res = test_query("show top 5 products by unit_price", session_id=session_id)
    
    # 2. If it interrupts, automatically approve it
    if res and res.get("status") == "interrupted":
        print("\nApproving SQL Execution (Resuming session)...")
        test_query("yes", session_id=session_id)
