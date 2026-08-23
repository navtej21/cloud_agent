package com.example.cloud_agent.websocket;

import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class SessionWebSocketHandler extends TextWebSocketHandler {

    // sessionId -> the open WebSocket connection watching it
    private final Map<String, WebSocketSession> connections = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String sessionId = extractSessionId(session);
        connections.put(sessionId, session);
        System.out.println("WebSocket connected for session: " + sessionId);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, org.springframework.web.socket.CloseStatus status) {
        String sessionId = extractSessionId(session);
        connections.remove(sessionId);
        System.out.println("WebSocket closed for session: " + sessionId);
    }

    private String extractSessionId(WebSocketSession session) {
       String path=session.getUri().getPath();
        return path.substring(path.lastIndexOf('/') + 1);
    }

    public void sendEvent(String sessionId, String message) {
        WebSocketSession session = connections.get(sessionId);
        if (session != null && session.isOpen()) {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (Exception e) {
                System.out.println("Failed to send WebSocket message: " + e.getMessage());
            }
        }
    }
}