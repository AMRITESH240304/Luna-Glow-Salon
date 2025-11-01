//
//  SupervisorModel.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import Foundation
import FirebaseFirestore

struct SupervisorModel: Codable, Identifiable {
    @DocumentID var id: String?
    let user_id: String
    let user_name: String
    let assigned_to: String
    let query: String
    let source: String
    let status: String
    let timestamp: String
}

struct SupervisorResponseModel: Codable {
    let supervisors: [SupervisorModel]
}
