package com.example.WebRemote.RESTcontroller;

import com.example.WebRemote.model.HealthStatusDTO;
import com.example.WebRemote.service.HealthStore;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/health")
public class HelthMonitor {

    private final HealthStore healthStore;

    public HelthMonitor(HealthStore healthStore) {
        this.healthStore = healthStore;
    }


    @PostMapping
    public ResponseEntity<String> updateHealth(@RequestBody HealthStatusDTO status) {
        healthStore.update(status);
        return ResponseEntity.ok("Health updated");
    }


    @GetMapping
    public ResponseEntity<HealthStatusDTO> getHealth() {
        return ResponseEntity.ok(healthStore.get());
    }
}
