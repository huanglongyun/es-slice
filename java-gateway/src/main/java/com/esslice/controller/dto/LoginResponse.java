package com.esslice.controller.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private UserInfo userInfo;

    @Data
    public static class UserInfo {
        private Long userId;
        private String username;
        private String realName;
        private String role;
    }
}
