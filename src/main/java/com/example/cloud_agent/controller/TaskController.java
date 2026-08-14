package com.example.cloud_agent.controller;


import com.example.cloud_agent.models.TaskRequest;
import com.example.cloud_agent.models.TaskResponse;
import com.example.cloud_agent.service.TaskService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TaskController {


    private final TaskService taskService;

    public TaskController(TaskService taskService){
        this.taskService=taskService;
    }



    @PostMapping("/tasks")
    public TaskResponse startTask(@RequestBody TaskRequest taskRequest){
        String sessionId=taskService.startTask(taskRequest.task());
        return new TaskResponse(sessionId,taskRequest.task());
    }
}
