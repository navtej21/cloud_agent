package com.example.cloud_agent.service;

import com.example.cloud_agent.enums.SessionEnum;
import com.example.cloud_agent.model.Session;
import com.example.cloud_agent.repo.SessionRepo;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Component
public class SessionStatusListener {

    private final StringRedisTemplate redisTemplate;
    private final SessionRepo sessionRepository;

    public SessionStatusListener(StringRedisTemplate redisTemplate, SessionRepo sessionRepository) {
        this.redisTemplate = redisTemplate;
        this.sessionRepository = sessionRepository;
    }

    @PostConstruct
    public void startListening() {
        System.out.print("Started");
        Thread listenerThread = new Thread(this::listen);
        listenerThread.setDaemon(true);
        listenerThread.start();
        System.out.print("listener thread called");
    }

    private void listen() {
        String lastId = "0-0";  // "$" = only new messages from when this thread starts

        while (true) {
            try {
                List<MapRecord<String, Object, Object>> messages =
                        redisTemplate.opsForStream()
                                .read(StreamOffset.create("session_status", ReadOffset.from(lastId)));

                if (messages == null || messages.isEmpty()) {
                    continue;
                }

                for (MapRecord<String, Object, Object> message : messages) {
                    lastId = message.getId().getValue();

                    String sessionId = (String) message.getValue().get("session_id");
                    String status = (String) message.getValue().get("status");

                    System.out.println("status"+status);

                    Optional<Session> sessionOpt = sessionRepository.findBySessionId(sessionId);

                    if (sessionOpt.isPresent()) {
                        Session session = sessionOpt.get();
                        session.setStatus(SessionEnum.valueOf(status));
                        sessionRepository.save(session);
                        System.out.println("Updated session " + sessionId + " to " + status);
                    } else {
                        System.out.println("No session found for id: " + sessionId);
                    }
                }

            } catch (Exception e) {
                System.out.println("Listener error: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }
}