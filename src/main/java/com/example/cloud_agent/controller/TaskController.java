package com.example.cloud_agent.controller;


import com.example.cloud_agent.model.Session;
import com.example.cloud_agent.models.TaskRequest;
import com.example.cloud_agent.models.TaskResponse;
import com.example.cloud_agent.repo.SessionRepo;
import com.example.cloud_agent.service.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@RestController
public class TaskController {


    private final TaskService taskService;
    private final SessionRepo sessionRepo;
    private final StringRedisTemplate redisTemplate;


    private final int MAX_REQUESTS_PER_WINDOW=10;
    private final Duration WINDOW_DURATION=Duration.ofSeconds(60);


    public TaskController(SessionRepo sessionRepo,TaskService taskService,StringRedisTemplate redisTemplate){
        this.taskService=taskService;
        this.sessionRepo=sessionRepo;
        this.redisTemplate=redisTemplate;
    }



    @PostMapping("/tasks")
    public ResponseEntity<?> startTask(@RequestBody TaskRequest request, HttpServletRequest httpRequest) {

        String clientId = httpRequest.getRemoteAddr();  // simplest identifier: caller's IP
        String rateLimitKey = "rate_limit:" + clientId;

        Long currentCount = redisTemplate.opsForValue().increment(rateLimitKey);

        if (currentCount == 1) {
            // first request in this window — start the expiry clock
            redisTemplate.expire(rateLimitKey, WINDOW_DURATION);
        }

        if (currentCount > MAX_REQUESTS_PER_WINDOW) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                    .body("Rate limit exceeded. Try again later.");
        }

        String sessionId = taskService.startTask(request.task());
        return ResponseEntity.ok(new TaskResponse(sessionId, "started"));
    }

    @GetMapping("/tasks/{sessionId}")
    public Session getTaskById(@PathVariable String sessionId){
        return sessionRepo.findBySessionId(sessionId).orElseThrow(()->{
            return new RuntimeException("No Tasks Found");
        });
    }
}

