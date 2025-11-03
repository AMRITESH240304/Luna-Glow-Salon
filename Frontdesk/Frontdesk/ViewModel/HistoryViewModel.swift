//
//  HistoryViewModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import Foundation
import FirebaseFirestore
import Combine

@MainActor
class HistoryViewModel: ObservableObject {
    @Published var allHistory: [HistoryModel] = []
    @Published var filteredHistory: [HistoryModel] = []
    @Published var selectedFilter: String = "All"

    private let db = Firestore.firestore()

    func fetchHistory() async {
        do {
            let snapshot = try await db.collection("history")
                .order(by: "resolved_at", descending: true)
                .getDocuments()

            let items = try snapshot.documents.compactMap { doc -> HistoryModel? in
                try doc.data(as: HistoryModel.self)
            }

            self.allHistory = items
            applyFilter()

        } catch {
            print("Error fetching history: \(error.localizedDescription)")
        }
    }

    func applyFilter() {
        switch selectedFilter {
        case "Resolved":
            filteredHistory = allHistory.filter { $0.status.lowercased() == "resolved" }
        case "Unresolved":
            filteredHistory = allHistory.filter { $0.status.lowercased() == "unresolved" }
        default:
            filteredHistory = allHistory
        }
    }
}
