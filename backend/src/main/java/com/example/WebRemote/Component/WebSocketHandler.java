package com.example.WebRemote.Component;

import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class WebSocketHandler extends AbstractWebSocketHandler {

    private final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();
    private final Map<String, String> sessionRoles = new ConcurrentHashMap<>(); // sessionId -> role
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void broadcastData(byte[] data) {
        for (WebSocketSession session : sessions) {
            if (session.isOpen()) {
                try {
                    // We simply send the binary data to everyone connected
                    // You can add logic here to filter by role (e.g., only send to "browser" role)
                    // Note: Creating a new BinaryMessage for each send is safer for buffer management
                    session.sendMessage(new BinaryMessage(data));
                } catch (IOException e) {
                    System.err.println("Error broadcasting to session " + session.getId() + ": " + e.getMessage());
                }
            }
        }
    }
    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
//        System.out.println("Received text message from session: " + session.getId());

        try {
            Map<String, Object> data = objectMapper.readValue(payload, Map.class);

            // Handle role identification (signaling)
            if (data.containsKey("role")) {
                String role = (String) data.get("role");
                sessionRoles.put(session.getId(), role);
//                System.out.println("Session " + session.getId() + " registered as: " + role);
                return;
            }

            // Relay signaling messages based on role
            String senderRole = sessionRoles.get(session.getId());
            if (senderRole != null) {
                for (WebSocketSession otherSession : sessions) {
                    if (otherSession != session && otherSession.isOpen()) {
                        String otherRole = sessionRoles.get(otherSession.getId());
                        // Only send to opposite role (pi <-> browser)
                        if (otherRole != null && !otherRole.equals(senderRole)) {
//                            System.out.println("Relaying text from " + senderRole + " to " + otherRole);
                            otherSession.sendMessage(new TextMessage(payload));
                        }
                    }
                }
            }

        } catch (Exception e) {
            System.err.println("Error processing text message: " + e.getMessage());
        }
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        ByteBuffer buffer = message.getPayload();
//        System.out.println("Received binary message from session: " + session.getId());

        String senderRole = sessionRoles.get(session.getId());
        // inside handleBinaryMessage
// ...
        if (senderRole != null) {
            for (WebSocketSession otherSession : sessions) {
                if (otherSession != session) {
                    String otherRole = sessionRoles.get(otherSession.getId());
                    if (otherRole != null && !otherRole.equals(senderRole)) {
                        // ADDED ROBUSTNESS CHECK AND ERROR HANDLING
                        if (otherSession.isOpen()) {
                            try {
                                otherSession.sendMessage(new BinaryMessage(buffer.duplicate(), true));
                            } catch (IOException e) {
                                System.err.println("Error sending message to session " + otherSession.getId() + ": " + e.getMessage());
                                // Optional: Close the session if a send error occurs to clean it up
                                if (e.getMessage().contains("Connection reset by peer")) {
                                    otherSession.close(); // Triggers afterConnectionClosed for cleanup
                                }
                            }
                        }
                    }
                }
            }
        }
// ... rest of the method

         else {
            // Fallback: if no role is set, broadcast to all (like old behavior)
            for (WebSocketSession otherSession : sessions) {
                if (otherSession != session && otherSession.isOpen()) {
                    otherSession.sendMessage(new BinaryMessage(buffer.duplicate(), true));
                }
            }
        }
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        sessions.add(session);
//        System.out.println("New connection: " + session.getId() + ", Total sessions: " + sessions.size());
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, org.springframework.web.socket.CloseStatus status) throws Exception {
        sessions.remove(session);
        sessionRoles.remove(session.getId());
//        System.out.println("Connection closed: " + session.getId() + ", Remaining sessions: " + sessions.size());
    }
}