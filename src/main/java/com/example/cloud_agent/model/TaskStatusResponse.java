package com.example.cloud_agent.model;


import lombok.Data;

import java.time.Instant;

@Data
public class TaskStatusResponse {

    private String sessionId;
    private String task;
    private String status;
    Instant createdAt;
    Instant updatedAt;
}
