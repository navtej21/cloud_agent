package com.example.cloud_agent.model;


import com.example.cloud_agent.enums.SessionEnum;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Entity
@Table(name = "session")
@Data
@NoArgsConstructor
public class Session {

    @Id
    private String sessionId;
    @Column
    private String taskDescription;
    @Enumerated(EnumType.STRING)
    private SessionEnum Status=SessionEnum.QUEUED;
    @Column
    private Instant createdAt=Instant.now();
    @Column
    private Instant updatedAt;


    public Session(String sessionId,String taskDescription){
        this.sessionId=sessionId;
        this.taskDescription=taskDescription;
    }
}
