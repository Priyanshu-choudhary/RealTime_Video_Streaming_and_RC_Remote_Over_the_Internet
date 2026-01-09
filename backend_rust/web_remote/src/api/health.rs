use axum::{
    extract::State,
    routing::get,
    Json, Router,
};

use crate::{
    app_state::AppState,
    domain::health::HealthStatus,
};

pub fn routes() -> Router<AppState> {
    Router::new().route("/health", get(get_health).post(update_health))
}

async fn get_health(
    State(state): State<AppState>,
) -> Json<HealthStatus> {
    Json(state.health_store.get())
}

async fn update_health(
    State(state): State<AppState>,
    Json(status): Json<HealthStatus>,
) -> Json<&'static str> {
    state.health_store.update(status);
    Json("Health updated")
}