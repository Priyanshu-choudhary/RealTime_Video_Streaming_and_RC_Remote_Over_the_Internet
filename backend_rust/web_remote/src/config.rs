use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub server_port: u16,
}

impl Config {
    pub fn from_env() -> Self {
        let server_port = env::var("SERVER_PORT")
            .unwrap_or_else(|_| "8080".to_string())
            .parse()
            .unwrap_or(8080);

        Config { server_port }
    }
}
