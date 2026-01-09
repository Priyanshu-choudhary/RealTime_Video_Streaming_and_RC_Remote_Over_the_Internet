use std::sync::Arc;
use tokio::sync::broadcast;
use axum::extract::ws::Message;
use crate::services::health_store::HealthStore;

#[derive(Clone)]
pub struct AppState {
    pub health_store: HealthStore,
    pub ws_broadcast: Arc<broadcast::Sender<Message>>,
}
