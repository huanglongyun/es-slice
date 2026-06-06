package com.esslice.controller;

import com.esslice.config.JwtTokenProvider;
import com.esslice.controller.dto.LoginRequest;
import com.esslice.controller.dto.LoginResponse;
import com.esslice.model.SysUser;
import com.esslice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @PostMapping("/login.do")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        Optional<SysUser> opt = userService.findByUsername(req.getUsername());
        if (!opt.isPresent() || opt.get().getStatus() == 0) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户名或密码错误"));
        }
        SysUser user = opt.get();
        if (!userService.verifyPassword(req.getPassword(), user.getPassword())) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户名或密码错误"));
        }
        String token = jwtTokenProvider.generateToken(
                user.getId(), user.getUsername(), user.getRole());

        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        LoginResponse.UserInfo info = new LoginResponse.UserInfo();
        info.setUserId(user.getId());
        info.setUsername(user.getUsername());
        info.setRealName(user.getRealName());
        info.setRole(user.getRole());
        resp.setUserInfo(info);

        return ResponseEntity.ok(Map.of("code", 0, "data", resp));
    }

    @PostMapping("/logout.do")
    public ResponseEntity<?> logout() {
        return ResponseEntity.ok(Map.of("code", 0, "message", "ok"));
    }

    @GetMapping("/userinfo.do")
    public ResponseEntity<?> userinfo() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "未认证"));
        }
        String username = auth.getName();
        Optional<SysUser> opt = userService.findByUsername(username);
        if (!opt.isPresent()) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户不存在"));
        }
        SysUser user = opt.get();
        LoginResponse.UserInfo info = new LoginResponse.UserInfo();
        info.setUserId(user.getId());
        info.setUsername(user.getUsername());
        info.setRealName(user.getRealName());
        info.setRole(user.getRole());
        return ResponseEntity.ok(Map.of("code", 0, "data", info));
    }
}
