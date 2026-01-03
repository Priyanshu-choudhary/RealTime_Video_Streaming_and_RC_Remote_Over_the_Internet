
package com.example.WebRemote.model;

public class HealthStatusDTO {

    private boolean connected;
    private long latency;          // ms
    private long upTime;            // seconds or ms (your choice)
    private String containerStatus; // RUNNING / STOPPED / ERROR

    public HealthStatusDTO() {}

    public boolean isConnected() {
        return connected;
    }

    public void setConnected(boolean connected) {
        this.connected = connected;
    }

    public long getLatency() {
        return latency;
    }

    public void setLatency(long latency) {
        this.latency = latency;
    }

    public long getUpTime() {
        return upTime;
    }

    public void setUpTime(long upTime) {
        this.upTime = upTime;
    }

    public String getContainerStatus() {
        return containerStatus;
    }

    public void setContainerStatus(String containerStatus) {
        this.containerStatus = containerStatus;
    }
}
