mod app;
mod api;
mod services;
mod domain;
mod app_state;

#[tokio::main]
async fn main() {
 app::run().await;
}
