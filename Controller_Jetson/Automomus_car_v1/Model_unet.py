import numpy as np
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit # This initializes CUDA context

# Must import cv2 because it is used for resizing and color conversion
import cv2 

# Define the logger here since it's used inside the class definition
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

class TensorRTUnetSegmentor:
    """
    Handles TensorRT engine loading and inference for the U-Net segmentation model.
    The class is initialized with all necessary dimensions from the main script.
    """
    def __init__(self, engine_path, model_input_h, model_input_w, output_width, output_height):
        
        # Store dimensions as instance variables
        self.MODEL_INPUT_H = model_input_h
        self.MODEL_INPUT_W = model_input_w
        self.OUTPUT_WIDTH = output_width
        self.OUTPUT_HEIGHT = output_height

        # 1. Load Engine
        print(f"Loading TensorRT engine from {engine_path}...")
        runtime = trt.Runtime(TRT_LOGGER)
        with open(engine_path, "rb") as f:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
        if not self.engine:
            raise RuntimeError(f"Failed to load TensorRT engine from {engine_path}")
            
        self.context = self.engine.create_execution_context()
        print("Engine loaded successfully.")
        
        # 2. Allocate I/O buffers (Host and Device)
        self.bindings = []
        self.output_binding = None
        self.output_shape = None
        
        for binding in self.engine:
            size = trt.volume(self.engine.get_binding_shape(binding)) * self.engine.max_batch_size
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))
            
            # Host memory (Page-locked for faster transfer)
            host_mem = cuda.pagelocked_empty(size, dtype)
            # Device memory
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            
            self.bindings.append(int(device_mem))

            if self.engine.binding_is_input(binding):
                self.input_shape = self.engine.get_binding_shape(binding)
                self.input_h_mem = host_mem
                self.input_d_mem = device_mem
            else:
                self.output_shape = self.engine.get_binding_shape(binding)
                self.output_h_mem = host_mem
                self.output_d_mem = device_mem
                self.output_name = binding
                self.output_dtype = dtype
                
        self.input_channels = self.input_shape[1] 

    def _preprocess(self, frame):
        """
        Converts BGR frame to required TensorRT input format
        (Normalized, FP32, HWC -> CHW)
        """

        # 1. Resize
        input_frame = cv2.resize(
            frame,
            (self.MODEL_INPUT_W, self.MODEL_INPUT_H)
        )

        # 2. BGR -> RGB (only if model expects RGB)
        input_frame = cv2.cvtColor(input_frame, cv2.COLOR_BGR2RGB)

        # 3. Normalize to [0, 1]
        input_data = input_frame.astype(np.float32) / 255.0

        # 4. HWC -> CHW
        input_data = input_data.transpose((2, 0, 1))

        # 5. Copy to pagelocked host memory
        np.copyto(self.input_h_mem, input_data.ravel())

        # 6. Transfer to device
        cuda.memcpy_htod(self.input_d_mem, self.input_h_mem)


    def _preprocess2(self, frame):
        # 1. Resize and Convert BGR to RGB
       input_frame = cv2.resize(frame, (self.MODEL_INPUT_W, self.MODEL_INPUT_H))
       input_frame = cv2.cvtColor(input_frame, cv2.COLOR_BGR2RGB)

        # 2. MATCH PYTORCH NORMALIZATION (The Missing Step)
       input_data = input_frame.astype(np.float32) / 255.0
       mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
       std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
       input_data = (input_data - mean) / std # This is what albumentations does
        
        # 3. HWC to CHW
        input_data = input_data.transpose((2, 0, 1))
        
        # 4. Flatten and copy to host memory
        np.copyto(self.input_h_mem, input_data.ravel())
        
        # 5. Transfer data to device
        cuda.memcpy_htod(self.input_d_mem, self.input_h_mem)



    def _postprocess(self):
        """Processes raw TensorRT output into a visual segmentation mask."""
        # 1. Transfer data from device to host
        cuda.memcpy_dtoh(self.output_h_mem, self.output_d_mem)

        # 2. Reshape output (e.g., (1, 1, H, W))
        output_data = self.output_h_mem.reshape(self.output_shape)
        
        # 3. Apply Sigmoid/Threshold (Assuming binary segmentation C=1)
        # Apply sigmoid to convert logits to probabilities
        segmentation_probs = 1.0 / (1.0 + np.exp(-output_data))
        
        # Squeeze batch and channel dimension (e.g., -> HxW)
        segmentation_map = segmentation_probs[0, 0, :, :]
        
        # Create binary mask 
        mask_np = (segmentation_map > 0.5).astype(np.uint8) * 255
        
        # 4. Resize mask back to original camera resolution
        mask_np = cv2.resize(mask_np, (self.OUTPUT_WIDTH, self.OUTPUT_HEIGHT), interpolation=cv2.INTER_NEAREST)
        
        return mask_np

    def infer(self, frame):
        """Runs the complete inference cycle and returns the segmentation mask."""
        self._preprocess(frame)
        
        # Execute inference
        self.context.execute_v2(bindings=self.bindings)
        
        # Postprocess and return the mask
        return self._postprocess()
