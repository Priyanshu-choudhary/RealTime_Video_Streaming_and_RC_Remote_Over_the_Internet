package com.example.WebRemote.RESTcontroller;

import com.example.WebRemote.Component.WebSocketHandler; // Import your handler
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DataConverter {

    // 1. Inject the WebSocketHandler
    @Autowired
    private WebSocketHandler webSocketHandler;

    @PostMapping(value = "/data", consumes = MediaType.APPLICATION_OCTET_STREAM_VALUE, produces = MediaType.TEXT_PLAIN_VALUE)
    public String handleBinary(@RequestBody byte[] raw) {

        webSocketHandler.broadcastData(raw);

        return "OK";
    }
}