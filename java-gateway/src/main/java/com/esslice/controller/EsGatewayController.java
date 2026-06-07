package com.esslice.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import javax.servlet.http.HttpServletRequest;
import java.net.URI;

@RestController
@RequestMapping("/api/es")
public class EsGatewayController {

    @Value("${app.python.base-url}")
    private String pythonBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /** 通用 JSON 请求代理 */
    @RequestMapping(value = "/**", method = {
            RequestMethod.GET, RequestMethod.POST,
            RequestMethod.PUT, RequestMethod.DELETE})
    public ResponseEntity<?> proxy(HttpServletRequest request, @RequestBody(required = false) String body) {
        try {
            String path = request.getRequestURI();
            // 文件上传不在此处理，由 ImportController 单独代理
            if (path.contains("/import") && request.getContentType() != null
                    && request.getContentType().contains("multipart")) {
                return ResponseEntity.status(400)
                        .body("{\"code\":400,\"message\":\"import request should not reach here\"}");
            }
            path = path.replaceFirst("/api", "");
            path = path.replaceAll("\\.do$", "");
            String query = request.getQueryString();
            String targetUrl = pythonBaseUrl + path;
            if (query != null) {
                targetUrl += "?" + query;
            }

            HttpMethod method = HttpMethod.valueOf(request.getMethod());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    URI.create(targetUrl), method, entity, String.class);

            return ResponseEntity.status(response.getStatusCode())
                    .body(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(500)
                    .body("{\"code\":500,\"message\":\"" + e.getMessage() + "\"}");
        }
    }
}
