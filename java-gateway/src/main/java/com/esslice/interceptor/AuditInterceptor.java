package com.esslice.interceptor;

import com.esslice.config.JwtTokenProvider;
import com.esslice.model.AuditLog;
import com.esslice.repository.AuditLogRepository;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
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

    @Value("${app.python.base-url}")
    private String pythonBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

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
        String beforeContent = "";
        String afterContent = "";

        if (path.endsWith("/import")) {
            action = "IMPORT";
            Object[] args = joinPoint.getArgs();
            if (args.length >= 2 && args[1] instanceof String) {
                indexName = (String) args[1];
                beforeContent = indexName;
            }
        } else if ("PUT".equals(method) && path.contains("/doc/")) {
            action = "UPDATE";
            docId = parts[parts.length - 1];
            indexName = parts.length > 4 ? parts[4] : "";
            // 获取更新前的文档内容
            beforeContent = fetchDocFromPython(indexName, docId);
        } else if ("DELETE".equals(method) && path.contains("/doc/")) {
            action = "DELETE";
            docId = parts[parts.length - 1];
            indexName = parts.length > 4 ? parts[4] : "";
            // 获取删除前的文档内容
            beforeContent = fetchDocFromPython(indexName, docId);
        } else if (path.endsWith("/export")) {
            action = "EXPORT";
            indexName = parts.length > 4 ? parts[4] : "";
            Object[] args = joinPoint.getArgs();
            if (args.length >= 2 && args[1] instanceof String) {
                beforeContent = ((String) args[1]).length() > 200
                        ? ((String) args[1]).substring(0, 200) + "..." : (String) args[1];
            }
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

        Object result = joinPoint.proceed();

        // 更新后获取新文档，保证 before/after 格式一致
        if (action.equals("UPDATE") && !indexName.isEmpty() && !docId.isEmpty()) {
            afterContent = fetchDocFromPython(indexName, docId);
        } else if (action.equals("IMPORT")) {
            afterContent = beforeContent;  // 导入操作，前后都是索引列表
        }

        AuditLog log = new AuditLog();
        log.setUserId(userId);
        log.setUsername(username);
        log.setAction(action);
        log.setIndexName(indexName);
        log.setDocId(docId);
        log.setBeforeContent(beforeContent);
        log.setAfterContent(afterContent);
        log.setIpAddress(getClientIp(request));
        auditLogRepository.save(log);

        return result;
    }

    /** 从 Python 服务获取当前文档内容（更新/删除前） */
    private String fetchDocFromPython(String indexName, String docId) {
        try {
            String url = pythonBaseUrl + "/es/indexes/" + indexName + "/doc/" + docId;
            ResponseEntity<String> resp = restTemplate.getForEntity(url, String.class);
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return resp.getBody();
            }
        } catch (Exception e) {
            return "{\"error\": \"无法获取原文档: " + e.getMessage() + "\"}";
        }
        return "";
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
