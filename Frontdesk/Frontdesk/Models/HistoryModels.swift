//
//  HistoryModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import Foundation
import FirebaseFirestore

struct HistoryModel: Codable, Identifiable {
    @DocumentID var id: String?
    let user_id: String
    let user_name: String
    let assigned_to: String
    let query: String
    let source: String
    let status: String
    let timestamp: String
    let response_message: String?
    let resolved_at: Date?
}
