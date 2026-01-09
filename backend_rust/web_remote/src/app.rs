use axum::Router;
use std::net::SocketAddr;
use tracing::info;
use std::sync::Arc;
use tokio::sync::broadcast;
use axum::extract::ws::Message;

use crate::{
    api,
    app_state::AppState,
    services::health_store::HealthStore,
};

pub async fn run() {
    // Global broadcast channel (Text + Binary)
    let (tx, _) = broadcast::channel::<Message>(100);
    let tx = Arc::new(tx);

    // Create unified app state
    let state = AppState {
        health_store: HealthStore::new(),
        ws_broadcast: tx,
    };

    let app = Router::new()
        .merge(api::routes(state));

    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    info!("Listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind port");

    axum::serve(listener, app).await.unwrap();
}