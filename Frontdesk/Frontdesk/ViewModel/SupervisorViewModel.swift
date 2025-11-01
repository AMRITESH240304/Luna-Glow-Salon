//
//  SupervisorViewModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import Foundation
import Combine
import FirebaseFirestore

@MainActor
class SupervisorViewModel: ObservableObject {
    @Published var supervisors: SupervisorResponseModel = .init(supervisors: [])
    
    private let db = Firestore.firestore()
    
    func fetchPendingRequests() async {
            do {
                let snapshot = try await db.collection("help_requests")
                    .whereField("status", isEqualTo: "pending")
                    .getDocuments()
                
                let requests = try snapshot.documents.compactMap { doc -> SupervisorModel? in
                    try doc.data(as: SupervisorModel.self)
                }
                
                self.supervisors = SupervisorResponseModel(supervisors: requests)
                
            } catch {
                print("❌ Error fetching requests: \(error.localizedDescription)")
            }
        }
    
    func updateRequestStatus(requestID: String, message: String, newStatus: String = "resolved") async {
            do {
                let requestRef = db.collection("help_requests").document(requestID)
                let snapshot = try await requestRef.getDocument()
                
                guard var data = snapshot.data() else {
                    print("❌ Document not found for ID: \(requestID)")
                    return
                }
                
                // Add response info and status
                data["status"] = newStatus
                data["response_message"] = message
                data["resolved_at"] = Timestamp(date: Date())
                
                // Move to 'history' collection
                try await db.collection("history").document(requestID).setData(data)
                
                // Remove from active help_requests
                try await requestRef.delete()
                
                print("✅ Moved request \(requestID) to history collection.")
                
                // Optionally, refresh the UI
                await fetchPendingRequests()
                
            } catch {
                print("❌ Error updating request status: \(error.localizedDescription)")
            }
        }
}
