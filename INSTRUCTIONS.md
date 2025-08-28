# Setting up the Local AI Model

This agent uses a local Large Language Model (LLM) to provide intelligent analysis of potential vulnerabilities. To use this feature, you need to download a model file.

**For the best performance, we strongly recommend using the following smaller, faster model.**

## 1. Download the Recommended Model (Phi-3 Mini)

The recommended model is a version of Microsoft's Phi-3 Mini, which provides an excellent balance of speed and reasoning quality.

1.  **Click this link to download the model file:**
    [https://huggingface.co/SanctumAI/Phi-3-mini-4k-instruct-GGUF/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf](https://huggingface.co/SanctumAI/Phi-3-mini-4k-instruct-GGUF/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf)

    This file is approximately 2.2 GB, which is much smaller and faster than the previous model.

2.  **Place the downloaded file in the project's root directory.** The application is specifically configured to look for a file named `phi-3-mini-4k-instruct.Q4_K_M.gguf`.

## 2. You're Ready!

Once the file is in the correct location, you can run the application, and the AI analysis features will be fully enabled with much better performance.
