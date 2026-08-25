package com.example.cloud_agent.controller;


import com.example.cloud_agent.model.Session;
import com.example.cloud_agent.model.TaskStatusResponse;
import com.example.cloud_agent.models.TaskRequest;
import com.example.cloud_agent.models.TaskResponse;
import com.example.cloud_agent.repo.SessionRepo;
import com.example.cloud_agent.service.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

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

       try{

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

       catch(RedisConnectionFailureException e){
           return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).build();
       }
    }

    @GetMapping("/task/{sessionId}")
    public ResponseEntity<?> getTask(@PathVariable String sessionId){

        Session session = sessionRepo.findBySessionId(sessionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Session not found"));


        TaskStatusResponse response=new TaskStatusResponse();
        response.setStatus(session.getStatus().toString());
        response.setSessionId(session.getSessionId());
        response.setUpdatedAt(session.getUpdatedAt());
        response.setCreatedAt(session.getCreatedAt());
        response.setTask(session.getTaskDescription());
        return ResponseEntity.ok().body(response);
    }
}

