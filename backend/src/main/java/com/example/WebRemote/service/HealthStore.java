package com.example.WebRemote.service;


import com.example.WebRemote.model.HealthStatusDTO;
import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicReference;

@Service
public class HealthStore {

    private final AtomicReference<HealthStatusDTO> currentHealth =
            new AtomicReference<>(new HealthStatusDTO());

    public HealthStatusDTO get() {
        return currentHealth.get();
    }

    public void update(HealthStatusDTO status) {
        currentHealth.set(status);
    }
}
