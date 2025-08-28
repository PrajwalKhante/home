# Setting up the Local AI Model

This agent uses a local Large Language Model (LLM) to provide intelligent analysis of potential vulnerabilities. To use this feature, you need to download a model file.

## 1. Download the Model

We recommend using the `Mistral-7B-Instruct-v0.2-code-ft` model, which is a powerful yet relatively small model that can run on most modern computers.

1.  **Click this link to download the model file:**
    [https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-code-ft-GGUF/resolve/main/mistral-7b-instruct-v0.2-code-ft.Q4_K_M.gguf](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-code-ft-GGUF/resolve/main/mistral-7b-instruct-v0.2-code-ft.Q4_K_M.gguf)

    This file is approximately 4.37 GB.

2.  **Place the downloaded file in the project's root directory.** The application will look for a file named `mistral-7b-instruct-v0.2-code-ft.Q4_K_M.gguf` in the main directory of the project.

## 2. You're Ready!

Once the file is in the correct location, you can run the application, and the AI analysis features will be fully enabled. There is no need for an API key.
