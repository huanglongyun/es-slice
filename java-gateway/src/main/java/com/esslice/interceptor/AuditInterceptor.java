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

    @Around("execution(* com.esslice.controller.EsGatewayController.proxy(..)) || execution(* com.esslice.controller.ImportController.proxyImport(..))")
    public Object audit(ProceedingJoinPoint joinPoint) throws Throwable {
        HttpServletRequest request = ((ServletRequestAttributes)
                RequestContextHolder.currentRequestAttributes()).getRequest();

        String method = request.getMethod();
        if (!("PUT".equals(method) || "POST".equals(method) || "DELETE".equals(method))) {
            return joinPoint.proceed();
        }

        String path = request.getRequestURI();
        path = path.replaceAll("\\.do$", "");
        String[] parts = path.split("/");
        String indexName = "";
        String action = "CREATE";
        String docId = "";

        if (path.endsWith("/import")) {
            action = "IMPORT";
            // 从 args 中获取 indexes 参数（ImportController.args[1] 是 indexes 字符串）
            Object[] args = joinPoint.getArgs();
            if (args.length >= 2 && args[1] instanceof String) {
                indexName = (String) args[1];
            }
        } else if ("PUT".equals(method) && path.contains("/doc/")) {
            action = "UPDATE";
            docId = parts[parts.length - 1];
            indexName = parts.length > 3 ? parts[3] : "";
        } else if ("DELETE".equals(method) && path.contains("/doc/")) {
            action = "DELETE";
            docId = parts[parts.length - 1];
            indexName = parts.length > 3 ? parts[3] : "";
        } else if (path.endsWith("/export")) {
            action = "EXPORT";
            indexName = parts.length > 3 ? parts[3] : "";
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

        // 安全获取请求体内容
        String requestBody = "";
        Object[] args = joinPoint.getArgs();
        if (args.length >= 2 && args[1] instanceof String) {
            requestBody = (String) args[1];
        }

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
