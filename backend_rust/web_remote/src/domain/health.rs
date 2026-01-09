use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    pub connected: bool,
    pub latency: u64,          // ms
    pub up_time: u64,          // seconds or ms
    pub container_status: String,
    pub last_message_time: u64,
}
