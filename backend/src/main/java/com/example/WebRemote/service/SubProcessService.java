package com.example.WebRemote.service;

import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.ProcessBuilder;

@Component
public class SubProcessService {

    private String line;
    private long pid;         // Java 9+ gives PID
    private boolean started = false;
    private String message = "";

    public Boolean setPb() throws IOException {
        //1. make a process builder.
        ProcessBuilder pb = new ProcessBuilder(
                //"python3", "main.py"          // Example: run python3 main.py
                // "bash", "stream.sh"        // Or: run a shell script
                "ls", "-la"                // Or: any system command
        );
        //Optional add working dir:
//        pb.directory(new File("C:\Users\DELL\Desktop\python"));
        // Optional: Merge error stream into output (easier to read)
        pb.redirectErrorStream(true);


        Process process = pb.start();

        // 3. Read the output (stdout + stderr)
        BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
        );


        while ((line = reader.readLine()) != null) {
            System.out.println(line);
        }

        pid = process.pid();  // Java 9+
        started = true;
        message = "Process started successfully with PID: " + pid;

        // DO NOT call process.waitFor() here!

        return true;
    }

//    String getOutput() {
//        return line;
//    }
}
