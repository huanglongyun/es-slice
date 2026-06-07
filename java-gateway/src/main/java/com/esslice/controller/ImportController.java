package com.esslice.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.net.URI;

@RestController
public class ImportController {

    @Value("${app.python.base-url}")
    private String pythonBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /** 文件导入代理 — 处理 multipart/form-data，独立路由避免被泛型代理拦截 */
    @PostMapping("/api/es/indexes/import.do")
    public ResponseEntity<?> proxyImport(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "indexes", defaultValue = "") String indexes,
            @RequestParam(value = "preview", defaultValue = "false") String preview) {
        try {
            String targetUrl = pythonBaseUrl + "/es/indexes/import";

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            });
            body.add("indexes", indexes);
            body.add("preview", preview);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    URI.create(targetUrl), HttpMethod.POST, entity, String.class);

            return ResponseEntity.status(response.getStatusCode())
                    .body(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(500)
                    .body("{\"code\":500,\"message\":\"" + e.getMessage() + "\"}");
        }
    }
}
