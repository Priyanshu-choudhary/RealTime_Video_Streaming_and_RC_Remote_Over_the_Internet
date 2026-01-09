pub mod hello;
pub mod ws;
pub mod health;

use axum::Router;
use crate::app_state::AppState;

//define all the routes here
pub fn routes(state: AppState) -> Router {
    Router::new()
        .merge(hello::routes())
        .merge(health::routes())
        .merge(ws::routes())
        .with_state(state)
}