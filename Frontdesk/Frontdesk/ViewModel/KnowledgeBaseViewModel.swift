//
//  KnowledgeBaseViewModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 03/11/25.
//

import Foundation
import FirebaseFirestore
import Combine

@MainActor
class KnowledgeBaseViewModel: ObservableObject {
    @Published var knowledgeBase: KnowledgeBaseResponseModel = .init(entries: [])
    
    private let db = Firestore.firestore()
    
    func fetchKnowledgeBase() async {
        do {
            let snapshot = try await db.collection("knowledge_base")
                .order(by: "created_at", descending: true)
                .getDocuments()
            
            let entries = try snapshot.documents.compactMap { doc -> KnowledgeBaseModel? in
                try doc.data(as: KnowledgeBaseModel.self)
            }
            
            self.knowledgeBase = KnowledgeBaseResponseModel(entries: entries)
            
        } catch {
            print("❌ Error fetching knowledge base: \(error.localizedDescription)")
        }
    }
}
