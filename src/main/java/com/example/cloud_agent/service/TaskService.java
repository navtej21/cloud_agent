package com.example.cloud_agent.service;


import com.example.cloud_agent.model.Session;
import com.example.cloud_agent.repo.SessionRepo;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;

@Service
public class TaskService {


    private final StringRedisTemplate redisTemplate;
    private final SessionRepo sessionRepo;

    public TaskService(SessionRepo sessionRepo,StringRedisTemplate redisTemplate){
        this.redisTemplate=redisTemplate;
        this.sessionRepo=sessionRepo;
    }


    public String startTask(String task){
        String sessionId= UUID.randomUUID().toString();
        Session session=new Session(sessionId,task);
        sessionRepo.save(session);
        try{
            redisTemplate.opsForStream().add("agent_tasks",Map.of("sessionId",sessionId,"tasks",task));
        }
        catch(RedisConnectionFailureException e){
            return "Redis Connection Failure";
        }
        return sessionId;
    }
}
