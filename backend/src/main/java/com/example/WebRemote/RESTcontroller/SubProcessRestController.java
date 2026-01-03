package com.example.WebRemote.RESTcontroller;

import com.example.WebRemote.service.SubProcessService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;

@RestController()
@RequestMapping("/subprocess")
public class SubProcessRestController {

    @Autowired
    private SubProcessService subProcessService;

   @GetMapping("/start")
   public ResponseEntity<String> startProcess() {
       try {
           subProcessService.setPb();
           return ResponseEntity.accepted().body("Process started successfully");
       } catch (IOException e) {
           return ResponseEntity.internalServerError().body("Failed to start process: " + e.getMessage());
       }
   }
}
