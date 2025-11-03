//
//  KnowledgeBaseModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 03/11/25.
//

import Foundation
import FirebaseFirestore

struct KnowledgeBaseModel: Codable, Identifiable {
    @DocumentID var id: String?
    let query: String
    let answer: String
    let source: String?
    let resolved_by: String?
    let created_at: Timestamp?
}

struct KnowledgeBaseResponseModel: Codable {
    let entries: [KnowledgeBaseModel]
}
