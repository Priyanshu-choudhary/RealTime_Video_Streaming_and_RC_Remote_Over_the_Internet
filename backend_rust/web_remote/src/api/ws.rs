use axum::{
    extract::{
        ws::{Message, WebSocket},
        State, WebSocketUpgrade,
    },
    response::IntoResponse,
    routing::get,
    Router,
};
use futures_util::{SinkExt, StreamExt};
use tokio::sync::mpsc;

use crate::app_state::AppState;

// Define routes for WebSocket
pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/ws", get(ws_handler))
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

async fn handle_socket(socket: WebSocket, state: AppState) {
    let tx = state.ws_broadcast.clone();
    let mut rx = tx.subscribe();

    let (mut ws_sender, mut ws_receiver) = socket.split();

    // Internal channel: many tasks -> single WebSocket sender
    let (out_tx, mut out_rx) = mpsc::unbounded_channel::<Message>();

    // ---- Task 1: ONLY task allowed to write to WebSocket ----
    let send_task = tokio::spawn(async move {
        while let Some(msg) = out_rx.recv().await {
            if ws_sender.send(msg).await.is_err() {
                break;
            }
        }
    });

    // Welcome message (only this client)
    let _ = out_tx.send(Message::Text("Welcome to WebSocket!".into()));

    // ---- Task 2: Broadcast -> client ----
    let out_tx_clone = out_tx.clone();
    let broadcast_task = tokio::spawn(async move {
        loop {
            match rx.recv().await {
                Ok(msg) => {
                    let _ = out_tx_clone.send(msg);
                }
                Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                    println!("Warning: Client lagged, skipped {n} messages");
                }
                Err(_) => break,
            }
        }
    });

    // ---- Task 3: Client -> broadcast ----
    let tx_clone = tx.clone();
    let recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = ws_receiver.next().await {
            match msg {
                Message::Text(text) => {
                    // Broadcast to all clients (including sender)
                    let _ = tx_clone.send(Message::Text(text));
                }
                Message::Binary(bytes) => {
                    // Broadcast to all clients (including sender)
                    let _ = tx_clone.send(Message::Binary(bytes));
                }
                Message::Ping(data) => {
                    let _ = out_tx.send(Message::Pong(data));
                }
                Message::Close(frame) => {
                    println!("Client closed: {:?}", frame);
                    break;
                }
                _ => {}
            }
        }
    });

    // Shutdown handling
    tokio::select! {
        _ = send_task => {},
        _ = broadcast_task => {},
        _ = recv_task => {},
    }

    println!("Client disconnected");
}
