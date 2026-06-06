package com.esslice.interceptor;

import com.esslice.config.JwtTokenProvider;
import com.esslice.model.AuditLog;
import com.esslice.repository.AuditLogRepository;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;

@Aspect
@Component
public class AuditInterceptor {

    @Autowired
    private AuditLogRepository auditLogRepository;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Around("execution(* com.esslice.controller.EsGatewayController.proxy(..))")
    public Object audit(ProceedingJoinPoint joinPoint) throws Throwable {
        HttpServletRequest request = ((ServletRequestAttributes)
                RequestContextHolder.currentRequestAttributes()).getRequest();

        String method = request.getMethod();
        if (!("PUT".equals(method) || "POST".equals(method) || "DELETE".equals(method))) {
            return joinPoint.proceed();
        }

        String path = request.getRequestURI();
        String[] parts = path.split("/");
        String indexName = parts.length > 3 ? parts[3] : "";
        String action = "CREATE";
        String docId = "";

        if ("PUT".equals(method) && path.contains("/doc/")) {
            action = "UPDATE";
            docId = parts[parts.length - 1];
        } else if ("DELETE".equals(method) && path.contains("/doc/")) {
            action = "DELETE";
            docId = parts[parts.length - 1];
        } else if (path.endsWith("/export")) {
            action = "EXPORT";
        } else if (path.endsWith("/import")) {
            action = "IMPORT";
        }

        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String username = auth != null ? auth.getName() : "unknown";
        Long userId = 0L;

        String token = (String) auth.getDetails();
        if (token != null) {
            try {
                userId = jwtTokenProvider.getUserIdFromToken(token);
            } catch (Exception ignored) {}
        }

        String requestBody = (String) joinPoint.getArgs()[1];
        Object result = joinPoint.proceed();

        AuditLog log = new AuditLog();
        log.setUserId(userId);
        log.setUsername(username);
        log.setAction(action);
        log.setIndexName(indexName);
        log.setDocId(docId);
        log.setBeforeContent(requestBody);
        log.setIpAddress(getClientIp(request));
        auditLogRepository.save(log);

        return result;
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        return ip;
    }
}
