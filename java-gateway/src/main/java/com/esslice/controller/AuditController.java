package com.esslice.controller;

import com.esslice.model.AuditLog;
import com.esslice.service.AuditService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/audit-logs")
public class AuditController {

    @Autowired
    private AuditService auditService;

    @GetMapping
    public ResponseEntity<?> query(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) String indexName,
            @RequestParam(required = false) String action,
            @RequestParam(required = false)
                @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startTime,
            @RequestParam(required = false)
                @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endTime,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize) {

        Page<AuditLog> result = auditService.query(
                username, indexName, action, startTime, endTime, page, pageSize);
        return ResponseEntity.ok(Map.of(
                "code", 0,
                "data", Map.of(
                        "total", result.getTotalElements(),
                        "list", result.getContent(),
                        "page", page,
                        "pageSize", pageSize
                )
        ));
    }
}
