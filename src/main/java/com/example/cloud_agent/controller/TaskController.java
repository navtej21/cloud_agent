package com.example.cloud_agent.controller;


import com.example.cloud_agent.model.Session;
import com.example.cloud_agent.models.TaskRequest;
import com.example.cloud_agent.models.TaskResponse;
import com.example.cloud_agent.repo.SessionRepo;
import com.example.cloud_agent.service.TaskService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class TaskController {


    private final TaskService taskService;
    private final SessionRepo sessionRepo;

    public TaskController(SessionRepo sessionRepo,TaskService taskService){
        this.taskService=taskService;
        this.sessionRepo=sessionRepo;
    }



    @PostMapping("/tasks")
    public TaskResponse startTask(@RequestBody TaskRequest taskRequest){
        String sessionId=taskService.startTask(taskRequest.task());
        return new TaskResponse(sessionId,taskRequest.task());
    }

    @GetMapping("/tasks/{id}")
    public Session getTaskById(@PathVariable String sessionId){
        return sessionRepo.findBySessionId(sessionId).orElseThrow(()->{
            return new RuntimeException("No Tasks Found");
        });
    }
}

