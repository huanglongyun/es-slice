package com.esslice;

import com.esslice.config.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    @BeforeEach
    void setUp() {
        jwtTokenProvider = new JwtTokenProvider();
        ReflectionTestUtils.setField(jwtTokenProvider, "secret",
                "test-secret-key-12345678901234567890");
        ReflectionTestUtils.setField(jwtTokenProvider, "expirationMs", 3600000L);
    }

    @Test
    void generateAndValidateToken() {
        String token = jwtTokenProvider.generateToken(1L, "admin", "admin");
        assertNotNull(token);
        assertTrue(jwtTokenProvider.validateToken(token));
    }

    @Test
    void parseUsernameFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "admin", "admin");
        assertEquals("admin", jwtTokenProvider.getUsernameFromToken(token));
    }

    @Test
    void parseRoleFromToken() {
        String token = jwtTokenProvider.generateToken(1L, "editor", "editor");
        assertEquals("editor", jwtTokenProvider.getRoleFromToken(token));
    }

    @Test
    void parseUserIdFromToken() {
        String token = jwtTokenProvider.generateToken(42L, "user1", "viewer");
        assertEquals(42L, jwtTokenProvider.getUserIdFromToken(token));
    }

    @Test
    void invalidTokenReturnsFalse() {
        assertFalse(jwtTokenProvider.validateToken("invalid.token.here"));
        assertFalse(jwtTokenProvider.validateToken(""));
        assertFalse(jwtTokenProvider.validateToken(null));
    }
}
