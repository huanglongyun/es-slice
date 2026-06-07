package com.esslice;

import com.esslice.model.SysUser;
import com.esslice.repository.UserRepository;
import com.esslice.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserService userService;

    @Test
    void findByUsername() {
        SysUser user = new SysUser();
        user.setUsername("admin");
        user.setRole("admin");
        when(userRepository.findByUsername("admin")).thenReturn(Optional.of(user));

        Optional<SysUser> found = userService.findByUsername("admin");
        assertTrue(found.isPresent());
        assertEquals("admin", found.get().getRole());
    }

    @Test
    void createUserEncodesPassword() {
        when(passwordEncoder.encode("plain123")).thenReturn("hashed_abc");
        when(userRepository.save(any(SysUser.class))).thenAnswer(inv -> inv.getArgument(0));

        SysUser user = new SysUser();
        user.setUsername("newuser");
        user.setPassword("plain123");
        SysUser created = userService.create(user);

        assertEquals("hashed_abc", created.getPassword());
    }

    @Test
    void verifyPassword() {
        when(passwordEncoder.matches("correct", "hashed")).thenReturn(true);
        assertTrue(userService.verifyPassword("correct", "hashed"));

        when(passwordEncoder.matches("wrong", "hashed")).thenReturn(false);
        assertFalse(userService.verifyPassword("wrong", "hashed"));
    }

    @Test
    void deleteUser() {
        userService.delete(1L);
        verify(userRepository).deleteById(1L);
    }
}
