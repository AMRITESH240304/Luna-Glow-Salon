//
//  SupervisorView.swift
//  Frontdesk
//
//  Created by Amritesh Kumar on 01/11/25.
//

import SwiftUI

struct SupervisorView: View {
    @StateObject private var viewModel = SupervisorViewModel()
    @State private var expandedRequestID: String? = nil
    @State private var responseMessages: [String: String] = [:]

    var body: some View {
        NavigationView {
            VStack(alignment: .leading) {
                Text("Pending Requests")
                    .font(.largeTitle)
                    .bold()
                    .padding(.top)

                List(viewModel.supervisors.supervisors) { item in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(item.user_name).font(.headline)
                                Text(item.query).font(.subheadline)
                            }
                            Spacer()
                            Button {
                                withAnimation {
                                    if expandedRequestID == item.id {
                                        expandedRequestID = nil
                                    } else {
                                        expandedRequestID = item.id
                                    }
                                }
                            } label: {
                                Image(systemName: expandedRequestID == item.id ? "chevron.down" : "chevron.right")
                                    .foregroundColor(.blue)
                                    .imageScale(.medium)
                            }
                        }

                        if expandedRequestID == item.id {
                            VStack(alignment: .leading, spacing: 6) {
                                TextField("Type your response...", text: Binding(
                                    get: { responseMessages[item.id ?? ""] ?? "" },
                                    set: { responseMessages[item.id ?? ""] = $0 }
                                ))
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                
                                HStack {
                                    Button("Mark Resolved") {
                                        Task {
                                            if let id = item.id,
                                               let message = responseMessages[id], !message.isEmpty {
                                                await viewModel.updateRequestStatus(requestID: id, message: message)
                                            }
                                        }
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .tint(.green)
                                    
                                    Button("Unresolved") {
                                        Task {
                                            if let id = item.id,
                                               let message = responseMessages[id], !message.isEmpty {
                                                await viewModel.updateRequestStatus(requestID: id, message: message, newStatus: "unresolved")
                                            }
                                        }
                                    }
                                    .buttonStyle(.bordered)
                                    .tint(.orange)
                                }
                            }
                            .padding(.top, 8)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .task {
                    await viewModel.fetchPendingRequests()
                }
            }
            .padding()
        }
    }
}


#Preview {
    SupervisorView()
}
