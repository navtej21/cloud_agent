package com.example.cloud_agent.service;


import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;

@Service
public class TaskService {


    private final StringRedisTemplate redisTemplate;

    public TaskService(StringRedisTemplate redisTemplate){
        this.redisTemplate=redisTemplate;
    }


    public String startTask(String task){
        String sessionId= UUID.randomUUID().toString();
        redisTemplate.opsForStream().add("agent_tasks",Map.of("sessionId",sessionId,"tasks",task));
        return sessionId;
    }
}
