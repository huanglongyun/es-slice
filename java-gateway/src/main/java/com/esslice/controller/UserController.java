package com.esslice.controller;

import com.esslice.model.SysUser;
import com.esslice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/list.do")
    public ResponseEntity<?> list() {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.listAll()));
    }

    @PostMapping("/create.do")
    public ResponseEntity<?> create(@RequestBody SysUser user) {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.create(user)));
    }

    @PutMapping("/{id}.do")
    public ResponseEntity<?> update(@PathVariable Long id, @RequestBody SysUser user) {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.update(id, user)));
    }

    @DeleteMapping("/{id}.do")
    public ResponseEntity<?> delete(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.ok(Map.of("code", 0, "message", "ok"));
    }
}
