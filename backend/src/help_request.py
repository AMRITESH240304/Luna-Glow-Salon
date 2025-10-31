# models/help_request.py

from dataclasses import dataclass, asdict
from datetime import datetime
import firebase_admin
from firebase_admin import firestore,credentials

cred = credentials.Certificate("/Users/amriteshkumar/Developer/frontdeskAssign/backend/firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@dataclass
class HelpRequest:
    query: str
    status: str = "pending"
    assigned_to: str = "supervisor_1"
    source: str = "LiveKitCall"
    timestamp: str = datetime.utcnow().isoformat()

    def save(self):
        """Save this HelpRequest to Firestore."""
        db.collection("help_requests").add(asdict(self))

    @staticmethod
    def list_pending():
        """Return all pending help requests."""
        docs = db.collection("help_requests").where("status", "==", "pending").stream()
        return [doc.to_dict() for doc in docs]

    @staticmethod
    def update_status(doc_id: str, new_status: str):
        """Update the status of an existing help request."""
        db.collection("help_requests").document(doc_id).update({"status": new_status})
