// !! Note !!
// This sample hardcodes a token which expires in 2 hours.
let wsURL = "wss://assignment-xo374h2l.livekit.cloud"
let token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjE5ODMxMTgsImlkZW50aXR5IjoiYW1yaXQiLCJpc3MiOiJBUElLaXMyejd3YjJZcDYiLCJuYmYiOjE3NjE5NzQxMTgsInN1YiI6ImFtcml0IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6Im1lIiwicm9vbUpvaW4iOnRydWV9fQ.9wZEVWUp67UtngRatKsq2pheLsNZ289ayURq2AYvDYA"
// In production you should generate tokens on your server, and your client
// should request a token from your server.
@preconcurrency import LiveKit
import LiveKitComponents
import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            TabView {
                SupervisorView()
                    .tabItem {
                        Label("Pending", systemImage: "hourglass")
                            .tag(0)
                    }
                
                HistoryView()
                    .tabItem {
                        Label("History", systemImage: "clock.arrow.circlepath")
                            .tag(1)
                    }
            }
        }
    }
}

//struct ContentView: View {
//    @StateObject private var room: Room
//
//    init() {
//        let room = Room()
//        _room = StateObject(wrappedValue: room)
//    }
//
//    var body: some View {
//        Group {
//            if room.connectionState == .disconnected {
//                Button("Connect") {
//                    Task {
//                        do {
//                            try await room.connect(
//                                url: wsURL,
//                                token: token,
//                                connectOptions: ConnectOptions(enableMicrophone: true)
//                            )
//                        } catch {
//                            print("Failed to connect to LiveKit: \(error)")
//                        }
//                    }
//                }
//            } else {
//                LazyVStack {
//                    
//                    ForEachParticipant { _ in
//                        VStack {
//                            Text("Connected to room: \(String(describing: room.name))")
//                                .font(.headline)
//                        }
//                    }
//                }
//            }
//        }
//        .padding()
//        .environmentObject(room)
//    }
//}
