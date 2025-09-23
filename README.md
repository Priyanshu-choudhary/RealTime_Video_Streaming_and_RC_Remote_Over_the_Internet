
---

# RealTime\_Video\_Streaming\_and\_RC\_Remote\_Over\_the\_Internet

🚀 **Low-latency video streaming and remote control system over the internet** using **WebRTC, WebSockets, and Dockerized Spring Boot backend**.
This project enables controlling hardware (motors, actuators, robots, etc.) remotely while streaming **real-time video** with **sub-100ms latency**.

---

## ✨ Features

* **Remote Control (RC) over WebSocket**

  * Sends **4-byte binary packets** from the web frontend.
  * EC2-hosted **Spring Boot WebSocket server** handles RC commands.
  * Jetson/Raspberry Pi client receives commands, decodes them, and forwards via **serial** to a motor driver.
  * Achieves **low-latency (<100ms)** communication.

* **Real-Time Video Streaming**

  * Implemented with **WebRTC** for efficient video transmission.
  * Custom **TURN server on AWS EC2** ensures connectivity across different networks.
  * **STUN + TURN + LAN fallback** ensures robust streaming anywhere (local LAN or internet).

* **Unified Signaling**

  * Same WebSocket connection handles both:

    * Binary RC packets
    * JSON signaling messages (WebRTC negotiation)
  * Efficient bandwidth usage with separated binary and JSON logic.

* **Dockerized Backend**

  * **Spring Boot server** runs inside Docker on AWS EC2.
  * Easy deployment, scaling, and management.

* **Cross-Hardware Support**

  * Works with **Jetson Nano** and **Raspberry Pi**.
  * Python WebSocket client for receiving control signals and handling motor commands.

---

## 🏗 System Architecture

```
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
```

---

## ⚡ Performance

* RC command latency: **<100ms**
* Video streaming: **Real-time via WebRTC**
* Bandwidth-efficient binary messaging
* Works across NAT/firewalls using TURN/STUN

---

## 🛠️ Installation & Setup

### 1. Backend (EC2 Spring Boot WebSocket Server)

* Clone repo on EC2 and run the spring boot manually using maven:

  ```bash
  git clone https://github.com/your-username/RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet.git
  cd RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet
  ```
* or Build and run inside Docker(easy):

  ```bash
    docker pull priyanshu1284/webremote-app:latest
    docker stop webremote-app && docker rm webremote-app            #stop and remove container  
    docker run -d -p 8080:8080 --name webremote-app priyanshu1284/webremote-app:latest	# Run the new container

  ```

### 2. TURN/STUN Server (for WebRTC)

* Deploy **coturn** on AWS EC2:

  ```bash
  sudo apt update
  sudo apt install coturn
  ```
* Configure `/etc/turnserver.conf` with:

  ```
  listening-port=3478
  fingerprint
  lt-cred-mech
  use-auth-secret
  static-auth-secret=your_secret_key
  realm=yourdomain.com
  total-quota=100
  ```
* Start the service:

  ```bash
  sudo service coturn start
  ```

### 3. Jetson/Raspberry Pi Client

* Install dependencies:

  ```bash
  sudo apt update
  sudo apt install python3-pip
  pip3 install websockets pyserial aiortc
  ```
* Run WebSocket + WebRTC client (run both the code as background task):

   RTC_Server.py       #Remember to change IP with your EC2 IP in baseURL
   main_Controller.py  #Remember to change with IP your EC2 IP in baseURL

  ```bash
  cd ./jetson_OR_RasberryPI_Remote_server
  bash run.sh
  ```

### 4. Frontend

* The frontend(React) is already hosted using the springboot static  folder if you use the Docker. 
* If you want to made any change then just go to frontent folder and run npm i and npm run dev.
* Now open frontend in browser with your ec2-ip:8080
* remote controller and Video stream will establish via WebRTC.

---

## 🚀 Usage

1. Start **backend WebSocket server** on EC2 uing Docker.
2. Ensure **TURN/STUN server** is running.
3. Run **run.sh** on Jetson/Raspberry Pi to handle RC + video streaming.
4. Open the **frontend in browser with your ec2 ip:8080** → Control RC & see video stream in real time.

---

## 📌 Roadmap

* ✅ **v1.0** – Working prototype with WebSocket + WebRTC integration.
* 🔧 **v2.0** – Further optimization (latency reduction, adaptive bitrate streaming).
* 🔒 Secure WebSocket (wss) & TURN with TLS.
* 📱 Mobile-friendly frontend.

---

## 🤝 Contributing

Pull requests and feature suggestions are welcome!

---

## 📜 License

This project is licensed under the **MIT License**.

---

