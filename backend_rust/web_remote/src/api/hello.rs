use axum::{routing::get, Router, Json};
use crate::services::hello_service;
use crate::app_state::AppState;

//Routers
pub fn routes() -> Router<AppState> {
    Router::new().route("/hello", get(hello))
}

//Handlers
async fn hello() -> Json<String> {
    let message = hello_service::get_hello_message();
    return Json(message);
}