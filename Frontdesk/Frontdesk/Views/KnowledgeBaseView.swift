//
//  KnowledgeBaseView.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 03/11/25.
//

import SwiftUI
import FirebaseCore

struct KnowledgeBaseView: View {
    @StateObject private var viewModel = KnowledgeBaseViewModel()
    @State private var expandedEntryID: String? = nil

    var body: some View {
        NavigationView {
            VStack(alignment: .leading) {
                Text("Knowledge Base")
                    .font(.largeTitle)
                    .bold()
                    .padding(.top)
                
                if viewModel.knowledgeBase.entries.isEmpty {
                    Spacer()
                    VStack {
                        ProgressView()
                        Text("Fetching knowledge base...")
                            .foregroundColor(.gray)
                            .padding(.top, 4)
                    }
                    Spacer()
                } else {
                    List(viewModel.knowledgeBase.entries) { item in
                        VStack(alignment: .leading) {
                                Button {
                                    withAnimation {
                                        expandedEntryID = (expandedEntryID == item.id) ? nil : item.id
                                    }
                                } label: {
                                    Image(systemName: expandedEntryID == item.id ? "chevron.down" : "chevron.right")
                                        .foregroundColor(.blue)
                                        .imageScale(.medium)
                                }
                            
                            if expandedEntryID == item.id {
                                Divider()
                                VStack(alignment: .leading, spacing: 6) {
                                    Text("Answer:")
                                        .font(.subheadline)
                                        .bold()
                                    Text(item.answer)
                                        .font(.body)
                                        .padding(.bottom, 6)
                                    
                                    if let resolvedBy = item.resolved_by {
                                        Text("Resolved by: \(resolvedBy)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    if let timestamp = item.created_at?.dateValue() {
                                        Text("Added on: \(timestamp.formatted(date: .abbreviated, time: .shortened))")
                                            .font(.caption2)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.top, 4)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .padding()
            .task {
                await viewModel.fetchKnowledgeBase()
            }
        }
    }
}

#Preview {
    KnowledgeBaseView()
}
