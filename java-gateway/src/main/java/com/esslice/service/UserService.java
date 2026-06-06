package com.esslice.service;

import com.esslice.model.SysUser;
import com.esslice.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    public Optional<SysUser> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    public List<SysUser> listAll() {
        return userRepository.findAll();
    }

    public SysUser create(SysUser user) {
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        return userRepository.save(user);
    }

    public SysUser update(Long id, SysUser user) {
        SysUser existing = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("用户不存在"));
        existing.setRealName(user.getRealName());
        existing.setEmail(user.getEmail());
        existing.setRole(user.getRole());
        existing.setStatus(user.getStatus());
        if (user.getPassword() != null && !user.getPassword().isEmpty()) {
            existing.setPassword(passwordEncoder.encode(user.getPassword()));
        }
        return userRepository.save(existing);
    }

    public void delete(Long id) {
        userRepository.deleteById(id);
    }

    public boolean verifyPassword(String raw, String encoded) {
        return passwordEncoder.matches(raw, encoded);
    }
}
