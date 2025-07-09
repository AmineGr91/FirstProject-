import os
import firebase_admin
from firebase_admin import credentials, firestore
import time

# --- Configuration ---
# Path to your downloaded service account key JSON file
# Make sure firebase_credentials.json is in the same directory as this script.
CREDENTIALS_FILE = 'firebase_credentials.json'

# --- Initialize Firebase Admin SDK ---
try:
    if not firebase_admin._apps: # Check if app is already initialized
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CREDENTIALS_FILE)
        
        if not os.path.exists(cred_path):
            print(f"ERROR: Credentials file not found at: {cred_path}")
            print("Please ensure 'firebase_credentials.json' is in the same directory as this script.")
            exit(1) # Exit if file not found
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully!")
    else:
        print("Firebase Admin SDK already initialized.")
    
    db = firestore.client()
    print("Firestore client obtained!")

except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Firebase Admin SDK or get Firestore client: {e}")
    print("Please check your 'firebase_credentials.json' file and internet connection.")
    exit(1) # Exit if initialization fails


# --- Test Firestore Operations ---
test_collection_name = 'test_collection'
test_doc_id = 'test_document'

def run_firestore_tests():
    print(f"\n--- Running Firestore Tests on collection '{test_collection_name}' ---")
    try:
        # 1. Write a document
        print("Attempting to write a test document...")
        doc_ref = db.collection(test_collection_name).document(test_doc_id)
        test_data = {
            'message': 'Hello from Flask project test script!',
            'timestamp': firestore.SERVER_TIMESTAMP # Use server timestamp
        }
        doc_ref.set(test_data) # Use set() to explicitly name the document
        print(f"Successfully wrote document '{test_doc_id}'.")

        time.sleep(1) # Give Firestore a moment to sync

        # 2. Read the document
        print("Attempting to read the test document...")
        read_doc = doc_ref.get()
        if read_doc.exists:
            print(f"Successfully read document '{read_doc.id}'. Data: {read_doc.to_dict()}")
        else:
            print(f"ERROR: Document '{test_doc_id}' does not exist after writing.")

        # 3. List documents in a collection (to test queries)
        print("Attempting to list documents in 'users' collection (for your registration test)...")
        # Ensure your Firestore rules allow 'allow read: if true;' for /users/{userId}
        users_docs = db.collection('users').limit(2).get() # Limit to avoid fetching too much
        user_count = 0
        if users_docs:
            for doc in users_docs:
                print(f"  User ID: {doc.id}, Data: {doc.to_dict().get('username')}")
                user_count += 1
        print(f"Found {user_count} documents in 'users' collection.")

        # 4. Attempt a query that might cause the hang (checking existing user)
        test_username_query = "temp_username_to_check" # Use a username you might try to register
        print(f"Attempting to query for username: '{test_username_query}'...")
        # Use FieldFilter as in your Flask app
        from google.cloud.firestore_v1.base_query import FieldFilter
        query_results = db.collection('users').where(filter=FieldFilter('username', '==', test_username_query)).limit(1).get()
        if len(query_results) > 0:
            print(f"Query found existing user: {query_results[0].id}")
        else:
            print(f"Query found no user with username: '{test_username_query}'")

        print("\n--- Firestore tests completed. ---")

    except Exception as e:
        print(f"ERROR: An exception occurred during Firestore operations: {e}")
        print("This could be due to: ")
        print("  - Incorrect Firestore Security Rules (Check 'Rules' tab in Firebase Console).")
        print("  - Network issues (Firewall, VPN, Proxy).")
        print("  - Invalid Firebase credentials (Ensure 'firebase_credentials.json' is valid).")
        import traceback
        traceback.print_exc() # Print full traceback for more details

if __name__ == "__main__":
    run_firestore_tests()
