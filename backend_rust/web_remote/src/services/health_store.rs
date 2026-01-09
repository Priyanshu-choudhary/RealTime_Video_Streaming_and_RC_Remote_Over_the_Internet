use std::sync::{Arc, RwLock};

use crate::domain::health::HealthStatus;

#[derive(Clone)]
pub struct HealthStore {
    inner: Arc<RwLock<HealthStatus>>,
}

impl HealthStore {
    pub fn new() -> Self {
        let initial = HealthStatus {
            connected: false,
            latency: 0,
            up_time: 0,
            container_status: "UNKNOWN".to_string(),
            last_message_time: 0,
        };

        Self {
            inner: Arc::new(RwLock::new(initial)),
        }
    }

    pub fn get(&self) -> HealthStatus {
        self.inner.read().unwrap().clone()
    }

    pub fn update(&self, status: HealthStatus) {
        *self.inner.write().unwrap() = status;
    }
}
