package com.esslice.model;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "audit_log")
public class AuditLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    @Column(length = 50)
    private String username;

    @Column(length = 50)
    private String action;

    @Column(name = "index_name", length = 100)
    private String indexName;

    @Column(name = "doc_id", length = 100)
    private String docId;

    @Column(name = "before_content", columnDefinition = "TEXT")
    private String beforeContent;

    @Column(name = "after_content", columnDefinition = "TEXT")
    private String afterContent;

    @Column(name = "ip_address", length = 50)
    private String ipAddress;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
