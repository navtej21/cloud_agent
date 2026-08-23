package com.example.cloud_agent.repo;

import com.example.cloud_agent.model.Session;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface SessionRepo extends  JpaRepository<Session,Long> {
    Optional<Session> findBySessionId(String sessionId);
}
