# RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet

## 🚀 Low-latency video streaming and remote control system over the internet using WebRTC, WebSockets, and Dockerized Spring Boot backend.
This project enables controlling hardware (motors, actuators, robots, etc.) remotely while streaming real-time video with sub-100ms latency.

✨ Features

## Remote Control (RC) over WebSocket

Sends 4-byte binary packets from the web frontend.

EC2-hosted Spring Boot WebSocket server handles RC commands.

Jetson/Raspberry Pi client receives commands, decodes them, and forwards via serial to a motor driver.

Achieves low-latency (<100ms) communication.

Real-Time Video Streaming

Implemented with WebRTC for efficient video transmission.

Custom TURN server on AWS EC2 ensures connectivity across different networks.

STUN + TURN + LAN fallback ensures robust streaming anywhere (local LAN or internet).

Unified Signaling

Same WebSocket connection handles both:

Binary RC packets

JSON signaling messages (WebRTC negotiation)

Efficient bandwidth usage with separated binary and JSON logic.

Dockerized Backend

Spring Boot server runs inside Docker on AWS EC2.

Easy deployment, scaling, and management.

Cross-Hardware Support

Works with Jetson Nano and Raspberry Pi.

Python WebSocket client for receiving control signals and handling motor commands.

```python 🏗 System Architecture
[Frontend Browser]
    |
    | (Binary RC packets + JSON signaling over WebSocket)
    v
[Spring Boot WebSocket Server on EC2 (Docker)]
    |
    |--> [Jetson/Raspberry Pi WebSocket Client]
    |         |--> Decode RC binary packets
    |         |--> Forward via Serial to Motor Driver
    |
    |--> [WebRTC Signaling Exchange]
              |
              |--> [WebRTC Peer Connection: Browser <-> Jetson/Pi]
                        (Video Streaming over STUN/TURN)

## ⚡ Performance

RC command latency: <100ms

Video streaming: Real-time via WebRTC

Bandwidth-efficient binary messaging

Works across NAT/firewalls using TURN/STUN

## 🛠️ Installation & Setup
### 1. Backend (EC2 Spring Boot WebSocket Server)

Clone repo on EC2:

git clone https://github.com/your-username/RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet.git
cd RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet/server

=================Docker Build for WebRemote on local/AWS EC2==========

Build and deploy using docker local:

docker build -t priyanshu1284/webremote-app:latest .		    #Build docker image
docker build --no-cache -t priyanshu1284/webremote-app:latest . #Build without chace
docker run -p 8080:8080 webremote-app  				            #Run locally
docker push priyanshu1284/webremote-app:latest			        #Push docker image to docker hub

#DOCKER On AWS server:

docker pull priyanshu1284/webremote-app:latest
docker stop webremote-app && docker rm webremote-app             #stop and remove container  
docker run -d -p 8080:8080 --name webremote-app priyanshu1284/webremote-app:latest	# Run the new container


### 2. TURN/STUN Server (for WebRTC)

Deploy coturn on AWS EC2:

```bash sudo apt update
```bash sudo apt install coturn


Configure /etc/turnserver.conf with:

listening-port=3478
fingerprint
lt-cred-mech
use-auth-secret
static-auth-secret=your_secret_key
realm=yourdomain.com
total-quota=100

eg.

listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0
external-ip=13.201.65.188/172.31.47.116

min-port=50000
max-port=60000

verbose
fingerprint
lt-cred-mech
realm=13.201.65.188
user=perceptron:root


Start the service:

sudo systemctl restart coturn

### 3. Jetson/Raspberry Pi Client

Install dependencies:

sudo apt update
sudo apt install python3-pip
pip3 install websockets pyserial aiortc


Run WebSocket + WebRTC client:

python3 client.py --server ws://<EC2-IP>:8080

### 4. Frontend

Open the frontend in browser (React/HTML app).

Connect to WebSocket server and start sending RC commands.

Video stream will establish via WebRTC.

## 🚀 Usage

Start backend WebSocket server on EC2.

Ensure TURN/STUN server is running.

Run client.py on Jetson/Raspberry Pi to handle RC + video streaming.

Open the frontend in browser → Control RC & see video stream in real time.

## 📌 Roadmap

✅ v1.0 – Working prototype with WebSocket + WebRTC integration.

🔧 v2.0 – Further optimization (latency reduction, adaptive bitrate streaming).

🔒 Secure WebSocket (wss) & TURN with TLS.

📱 Mobile-friendly frontend.

🤝 Contributing

Pull requests and feature suggestions are welcome!

## 📜 License

This project is licensed under the MIT License.


