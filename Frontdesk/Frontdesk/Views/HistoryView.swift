//
//  HistoryView.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import SwiftUI

struct HistoryView: View {
    @StateObject private var viewModel = HistoryViewModel()

    var body: some View {
        NavigationView {
            VStack(alignment: .leading) {
                Text("History")
                    .font(.largeTitle)
                    .bold()
                    .padding(.top)

                Picker("Status", selection: $viewModel.selectedFilter) {
                    Text("All").tag("All")
                    Text("Resolved").tag("Resolved")
                    Text("Unresolved").tag("Unresolved")
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .onChange(of: viewModel.selectedFilter) { oldValue, newValue in
                    viewModel.applyFilter()
                }

                List(viewModel.filteredHistory) { item in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(item.user_name).font(.headline)
                            Spacer()
                            Text(item.status.capitalized)
                                .font(.caption)
                                .padding(6)
                                .background(item.status.lowercased() == "resolved" ? .green.opacity(0.2) : .orange.opacity(0.2))
                                .cornerRadius(6)
                        }

                        Text("Query: \(item.query)")
                            .font(.subheadline)

                        if let message = item.response_message {
                            Text("Response: \(message)")
                                .font(.footnote)
                                .foregroundColor(.gray)
                        }

                        if let date = item.resolved_at {
                            Text("Resolved: \(date.formatted())")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
                .task {
                    await viewModel.fetchHistory()
                }
            }
            .padding(.horizontal)
        }
    }
}

#Preview {
    HistoryView()
}
