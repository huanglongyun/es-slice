package com.esslice.service;

import com.esslice.model.AuditLog;
import com.esslice.repository.AuditLogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import javax.persistence.criteria.Predicate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class AuditService {

    @Autowired
    private AuditLogRepository auditLogRepository;

    public Page<AuditLog> query(String username, String indexName,
                                 String action, LocalDateTime startTime,
                                 LocalDateTime endTime, int page, int size) {
        Specification<AuditLog> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (StringUtils.hasText(username)) {
                predicates.add(cb.like(root.get("username"), "%" + username + "%"));
            }
            if (StringUtils.hasText(indexName)) {
                predicates.add(cb.equal(root.get("indexName"), indexName));
            }
            if (StringUtils.hasText(action)) {
                predicates.add(cb.equal(root.get("action"), action));
            }
            if (startTime != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"), startTime));
            }
            if (endTime != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("createdAt"), endTime));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Pageable pageable = PageRequest.of(page - 1, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        return auditLogRepository.findAll(spec, pageable);
    }
}
