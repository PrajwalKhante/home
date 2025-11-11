# Compute Requirements

This document outlines the recommended hardware and software specifications for running this project. The requirements are broken down by task, as some parts of the pipeline are more resource-intensive than others.

## Minimum Requirements

These specifications should be sufficient for running the ETL pipeline, the Flask application, and performing inference with the pre-trained models.

-   **CPU:** Dual-core processor (e.g., Intel Core i3 or equivalent)
-   **RAM:** 8 GB
-   **Storage:** 10 GB of free space (for datasets, models, and dependencies)
-   **Operating System:** Windows 10/11, macOS, or a modern Linux distribution (e.g., Ubuntu 20.04+)
-   **Python Version:** 3.8+

## Recommended Requirements for Model Training

Training the machine learning models, especially the DistilBERT transformer, is significantly more demanding. For a reasonable training time, we recommend the following:

-   **CPU:** Quad-core processor or better (e.g., Intel Core i7 or AMD Ryzen 7)
-   **RAM:** 16 GB or more
-   **GPU:** An NVIDIA GPU with CUDA support is highly recommended for training the transformer model.
    -   **VRAM:** 6 GB+ (e.g., NVIDIA GeForce RTX 2060 or better)
    -   **Software:** CUDA Toolkit and cuDNN installed.
-   **Storage:** 20 GB of free space.

## Software Dependencies

All required Python packages are listed in the `requirements.txt` file. You can install them using:
```bash
pip install -r requirements.txt
```
For GPU support with PyTorch, you may need to install a specific version that matches your CUDA toolkit. Please refer to the [official PyTorch installation guide](https://pytorch.org/get-started/locally/) for detailed instructions.

## Reinforcement Learning Training

The RL training process is more CPU-bound than GPU-bound for this environment. The recommended training specs are suitable. The primary requirement is a stable network connection to the target application being tested.

## Summary

| Task                  | Minimum Specs                        | Recommended Specs                    | Notes                               |
| --------------------- | ------------------------------------ | ------------------------------------ | ----------------------------------- |
| **ETL & Data Proc**   | 8 GB RAM, Dual-core CPU              | 16 GB RAM, Quad-core CPU             | Network-intensive.                  |
| **TF-IDF Training**   | 8 GB RAM, Dual-core CPU              | 16 GB RAM, Quad-core CPU             | CPU-intensive.                      |
| **Transformer Training**| 8 GB RAM, Quad-core CPU              | 16 GB RAM, NVIDIA GPU (6GB+ VRAM)    | **GPU is highly recommended.**      |
| **Flask App & API**   | 8 GB RAM, Dual-core CPU              | 8 GB RAM, Dual-core CPU              | Lightweight.                        |
| **RL Agent Training** | 8 GB RAM, Dual-core CPU              | 16 GB RAM, Quad-core CPU             | CPU and Network-intensive.          |
