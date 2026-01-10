<div align="center">

# 🚗 Vision-Only Autonomous Vehicle Platform

### Deep Learning Powered | TensorRT Optimized | Sensor-Free Navigation

![TensorRT](https://img.shields.io/badge/TensorRT-Optimized-76B900?style=for-the-badge&logo=nvidia)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Jetson](https://img.shields.io/badge/Jetson-Edge%20AI-00A86B?style=for-the-badge&logo=nvidia)
![Deep Learning](https://img.shields.io/badge/Deep%20Learning-Vision%20Only-FF6F00?style=for-the-badge&logo=tensorflow)
![Real-time](https://img.shields.io/badge/Inference-12%20FPS-blue?style=for-the-badge)

**A fully autonomous vehicle system that uses ONLY a camera for perception, navigation, and control — no LiDAR, no Radar, no GPS, no Sonar. Pure Deep Learning.**

[Architecture](#-system-architecture) • [AI Pipeline](#-ai-pipeline) • [TinyTLV Protocol](#-tinytlv-binary-protocol) • [Demo](#-quick-start)

</div>

---

## 🎯 Project Highlights

| Feature | Description |
|---------|-------------|
| **🔭 Vision-Only Perception** | No LiDAR, Radar, GPS, or ultrasonic sensors — just a webcam |
| **🧠 Custom Neural Architecture** | TinyUNET + embedded CornerNet for joint segmentation & detection |
| **⚡ Edge-Optimized Inference** | TensorRT FP16 quantization achieving 12 FPS on Jetson Nano |
| **📡 TinyTLV Binary Protocol** | Custom ultra-compact protocol for sub-100ms end-to-end latency |
| **🎮 Full-Stack Remote Control** | Web dashboard with live video, telemetry, and manual override |
| **🛣️ Graph-Based Path Planning** | Real-time waypoint generation within drivable zones |

---

## 🏆 Key Innovations

### 1. Sensor-Free Autonomous Driving
Unlike traditional autonomous vehicles that rely on expensive sensor suites (LiDAR: $10,000+, Radar: $500+), this project achieves full autonomy using **only a $20 webcam**. All perception, localization, and decision-making is powered by deep learning.

### 2. Unified Perception Model (TinyUNET + CornerNet)
A single optimized neural network performs both:
- **Semantic Segmentation** — Road vs obstacles classification
- **Object Detection** — Bounding box detection for obstacles

By embedding CornerNet's corner detection mechanism into TinyUNET's decoder, we eliminate the need for separate models, reducing latency by ~40%.

### 3. TinyTLV: Ultra-Compact Binary Protocol
Custom-designed binary protocol that achieves:
- **4-12 byte packets** vs 100+ bytes for JSON
- **Works over any medium** — WiFi, Serial, LoRa, Ethernet
- **Zero-copy decoding** — Parse directly from byte stream
- **Bidirectional** — Same protocol from browser → cloud → Jetson → motor controller

---

## 🧠 AI Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PERCEPTION → PLANNING → CONTROL                       │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌────────────────────────┐      ┌─────────────────────┐
    │   Camera     │      │   TinyUNET + CornerNet │      │   Drivable Area     │
    │   Frame      │ ───▶ │   (TensorRT FP16)      │ ───▶ │   Mask + BBoxes     │
    │   640×480    │      │   ~83ms inference      │      │   Binary Mask       │
    └──────────────┘      └────────────────────────┘      └──────────┬──────────┘
                                                                     │
                                                                     ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              PATH PLANNING MODULE                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────────────┐│
│  │ Waypoint Gen    │───▶│ Graph-Based      │───▶│ Trajectory with              ││
│  │ in Drivable Zone│    │ Path Planning    │    │ Steering Angles              ││
│  └─────────────────┘    └──────────────────┘    └──────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
                                                                     │
                                                                     ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                              PID CONTROLLER                                   │
    │                                                                              │
    │   Target Angle ───▶ [ P: 4.0 | I: 1.0 | D: 0.01 ] ───▶ Motor PWM Commands   │
    │                                                                              │
    │   Future: Model Predictive Control (MPC) for smoother trajectories          │
    └──────────────────────────────────────────────────────────────────────────────┘
                                                                     │
                                                                     ▼
    ┌──────────────┐      ┌────────────────────┐      ┌─────────────────────────┐
    │  TinyTLV     │      │   Serial/UART      │      │   Motor Controller      │
    │  Encoder     │ ───▶ │   115200 baud      │ ───▶ │   (Arduino/ESC)         │
    └──────────────┘      └────────────────────┘      └─────────────────────────┘
```

---

## 🔬 Model Architecture: TinyUNET + CornerNet

### Why This Design?

| Challenge | Traditional Approach | Our Solution |
|-----------|----------------------|--------------|
| Need segmentation AND detection | Run 2 models sequentially | Single unified model |
| Limited edge compute | Heavy models (100+ MB) | 31 MB TensorRT engine |
| High latency | 200ms+ total | 83ms single forward pass |
| Memory constraints | 4GB+ VRAM needed | Runs on 4GB Jetson Nano |

### Architecture Details

```
Input: 640×480 RGB Image
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                    MobileNetV2 Encoder                          │
│  Layer 1: 320×240×32  ──┐                                       │
│  Layer 2: 160×120×64  ──┼── Skip Connections                    │
│  Layer 3: 80×60×128   ──┤                                       │
│  Layer 4: 40×30×256   ──┘                                       │
│  Bottleneck: 20×15×512                                          │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                    TinyUNET Decoder                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Embedded CornerNet Head (at 80×60 resolution)           │  │
│  │  • Top-Left Heatmap                                      │  │
│  │  • Bottom-Right Heatmap                                  │  │
│  │  • Corner Embeddings for Association                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Upsampling path with skip connections                          │
│  Final: 640×480×2 (Road, Obstacle classes)                     │
└────────────────────────────────────────────────────────────────┘
         │
         ├──────────────▶ Segmentation Mask (Drivable Area)
         │
         └──────────────▶ Bounding Boxes (Detected Obstacles)
```

### TensorRT Optimization

```python
# Optimization pipeline
Original PyTorch Model (89 MB, FP32)
    │
    ├── ONNX Export with dynamic axes
    │
    ▼
TensorRT Engine (31 MB, FP16)
    │
    ├── Layer fusion (Conv+BN+ReLU → single kernel)
    ├── FP16 quantization (2× memory reduction)
    ├── Kernel auto-tuning for Jetson architecture
    │
    ▼
Performance: 83ms inference @ 12 FPS
```

---

## 📡 TinyTLV Binary Protocol

### The Problem
Traditional IoT protocols waste bandwidth:
- JSON: `{"throttle": 1500, "steering": 1500}` = **42 bytes**
- Our TinyTLV: Same data in **6 bytes**

### Protocol Specification

```
┌───────────────────────────────────────────────────────────────┐
│                    TinyTLV Packet Structure                    │
├───────────────────────────────────────────────────────────────┤
│  Byte 0   │  Byte 1   │  Byte 2..N-1        │  Byte N        │
│  TYPE     │  LENGTH   │  VALUE (N-2 bytes)  │  CHECKSUM      │
│  (1 byte) │  (1 byte) │  (variable)         │  (1 byte)      │
└───────────────────────────────────────────────────────────────┘

Type Codes:
  0x01 = RC_THROTTLE     (2 bytes: uint16 PWM value)
  0x02 = RC_STEERING     (2 bytes: uint16 PWM value)  
  0x03 = RC_AUX          (3 bytes: channel + uint16)
  0x10 = TELEMETRY       (variable: sensor data)
  0x20 = COMMAND         (variable: string command)
  0xFF = HEARTBEAT       (0 bytes)
```

### Communication Flow

```
┌─────────────┐    WebSocket     ┌─────────────┐    WebSocket     ┌─────────────┐
│   Browser   │ ◀──(TinyTLV)───▶ │  Rust/Java  │ ◀──(TinyTLV)───▶ │   Jetson    │
│   Frontend  │    Binary        │   Server    │    Binary        │   Nano      │
└─────────────┘                  └─────────────┘                  └──────┬──────┘
                                                                         │
                                                                    Serial UART
                                                                    (TinyTLV)
                                                                         │
                                                                         ▼
                                                                  ┌─────────────┐
                                                                  │   Arduino   │
                                                                  │   Motor     │
                                                                  │   Control   │
                                                                  └─────────────┘
```

### Benefits

| Metric | JSON/REST | TinyTLV | Improvement |
|--------|-----------|---------|-------------|
| Packet Size | 50-200 bytes | 4-12 bytes | **10-20× smaller** |
| Parse Time | 5-10ms | <0.1ms | **50-100× faster** |
| Bandwidth | 50+ KB/s | 5 KB/s | **10× reduction** |
| Works over Serial | ❌ | ✅ | Unified protocol |

---

## 🏗 System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  USER INTERFACE                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  React/Remix Web Dashboard                                                  │ │
│  │  • Live GStreamer video feed (H.264/MJPEG)                                 │ │
│  │  • Real-time telemetry graphs                                               │ │
│  │  • Manual RC override controls                                              │ │
│  │  • Autonomous mode toggle                                                   │ │
│  │  • PID tuning interface                                                     │ │
│  │  • Web terminal for diagnostics                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ WebSocket (TinyTLV + Signaling)
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               CLOUD BACKEND                                       │
│  ┌──────────────────────────────┐    ┌─────────────────────────────────────────┐ │
│  │  Rust Axum Server             │    │  Health Monitoring                     │ │
│  │  • WebSocket multiplexer      │    │  • Connection status                   │ │
│  │  • TinyTLV router             │    │  • Latency tracking                    │ │
│  │  • Session management         │    │  • Uptime monitoring                   │ │
│  └──────────────────────────────┘    └─────────────────────────────────────────┘ │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ WebSocket (TinyTLV)
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          JETSON NANO EDGE COMPUTER                                │
│                                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────────┐ │
│  │ Video Pipeline  │  │  AI Inference   │  │  Control System                  │ │
│  │                 │  │                 │  │                                  │ │
│  │ • GStreamer     │  │ • TensorRT      │  │ • RC Mixer (Manual + Auto)      │ │
│  │ • H.264 encode  │  │ • TinyUNET      │  │ • PID Controller                │ │
│  │ • RTP streaming │  │ • Path Planner  │  │ • TinyTLV Serial Output         │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────────────┘ │
│                                                                                   │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ Serial UART (TinyTLV, 115200 baud)
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           LOW-LEVEL MOTOR CONTROLLER                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │  Arduino/ESP32                                                               ││
│  │  • TinyTLV decoder                                                           ││
│  │  • PWM signal generation                                                     ││
│  │  • ESC/Servo control                                                         ││
│  │  • Failsafe (neutral on disconnect)                                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Performance Benchmarks

### AI Inference (Jetson Nano 4GB)

| Model Variant | Precision | Size | Inference Time | FPS |
|---------------|-----------|------|----------------|-----|
| TinyUNET (PyTorch) | FP32 | 89 MB | 245ms | 4.1 |
| TinyUNET (ONNX) | FP32 | 85 MB | 180ms | 5.5 |
| **TinyUNET (TensorRT)** | **FP16** | **31 MB** | **83ms** | **12** |

### End-to-End Latency

| Stage | Latency | Notes |
|-------|---------|-------|
| Camera Capture | 8ms | USB webcam frame grab |
| AI Inference | 83ms | TensorRT FP16 |
| Path Planning | 12ms | Graph-based algorithm |
| PID Computation | <1ms | Simple arithmetic |
| TinyTLV Encode | <0.1ms | Zero-copy serialization |
| Serial TX | 2ms | 115200 baud UART |
| **Total Perception-to-Action** | **~106ms** | **~9.4 Hz control loop** |

### Communication Latency

| Path | Typical Latency | Max Latency |
|------|-----------------|-------------|
| Browser → Cloud | 30-50ms | 100ms |
| Cloud → Jetson | 20-40ms | 80ms |
| Jetson → Motor | 2-5ms | 10ms |
| **Total Round-Trip** | **52-95ms** | **190ms** |

---

## 📁 Project Structure

```
RealTime_Video_Streaming_and_RC_Remote/
│
├── 🧠 Controller_Jetson/              # Edge AI & Control System
│   └── Automomus_car_v1/
│       ├── Model_unet.py              # TinyUNET + CornerNet architecture
│       ├── PID_Controll.py            # PID controller implementation
│       ├── tinytlvx.py                # TinyTLV protocol encoder/decoder
│       ├── rc_mixer.py                # Manual/Autonomous command mixer
│       ├── main_client.py             # Main orchestrator
│       ├── serialSender.py            # UART communication
│       ├── health_monitor.py          # System health tracking
│       └── unet_mobilenetv2.engine    # TensorRT optimized model (31MB)
│
├── 🖥️ backend_rust/                   # Cloud Backend (Rust/Axum)
│   └── web_remote/
│       ├── src/
│       │   ├── api/                   # REST & WebSocket endpoints
│       │   ├── services/              # Business logic
│       │   ├── domain/                # Data models
│       │   └── app.rs                 # Application entry
│       └── Cargo.toml                 # Dependencies
│
├── 🎨 frontend-Remix/                 # Web Dashboard (React/Remix)
│   └── WebController/
│       └── app/
│           ├── routes/                # Dashboard pages
│           ├── components/            # UI components
│           └── utils/                 # Helpers & hooks
│
├── 🐳 Dockerfile                      # Container configuration
└── 📖 README.md                       # You are here
```

---

## 🚀 Quick Start

### Prerequisites

- **Jetson Nano** (4GB recommended) or **Jetson Orin Nano**
- **USB Webcam** (any standard webcam, 640×480 or higher)
- **Arduino/ESP32** for motor control
- **Node.js 18+** and **Rust 1.70+** for development

### 1. Clone and Setup

```bash
git clone https://github.com/Priyanshu-choudhary/RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet.git
cd RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet
```

### 2. Deploy Backend (Rust)

```bash
cd backend_rust/web_remote
cargo build --release
cargo run --release
# Server starts on http://localhost:8080
```

### 3. Setup Jetson Nano

```bash
cd Controller_Jetson/Automomus_car_v1

# Install dependencies
pip3 install opencv-python-headless numpy websockets pyserial

# Ensure TensorRT is installed (comes with JetPack)
# Copy your trained .engine file to this directory

# Run the autonomous system
python3 main_client.py
```

### 4. Launch Frontend

```bash
cd frontend-Remix/WebController
npm install
npm run dev
# Dashboard at http://localhost:5173
```

---

## 🎓 Research Context

This project demonstrates several key concepts in autonomous systems:

### Computer Vision
- **End-to-end learning**: Single model for perception and detection
- **Multi-task learning**: Joint segmentation and object detection
- **Edge deployment**: TensorRT optimization for embedded systems

### Control Theory
- **PID Control**: Classical feedback control for steering
- **Path planning**: Graph-based trajectory optimization
- **Sensor fusion**: (Vision-only, demonstrating feasibility without expensive sensors)

### Systems Engineering
- **Protocol design**: Custom binary protocol for IoT constraints
- **Real-time systems**: Sub-100ms control loop latency
- **Distributed systems**: Cloud-edge-device architecture

---

## 🗺️ Roadmap

- [x] **v1.0** — Basic remote control with video streaming
- [x] **v2.0** — TinyUNET segmentation model
- [x] **v3.0** — CornerNet integration for detection
- [x] **v4.0** — TensorRT optimization (12 FPS achieved)
- [x] **v5.0** — TinyTLV binary protocol
- [x] **v6.0** — Graph-based path planning
- [ ] **v7.0** — Model Predictive Control (MPC)
- [ ] **v8.0** — Multi-camera support
- [ ] **v9.0** — Night vision / IR camera support

---

## 👨‍💻 Author

**Yadi Chaudhary** — *AI/ML & Autonomous Systems*

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

*Proving that autonomous driving doesn't require expensive sensors — just clever AI.*

</div>