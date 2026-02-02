---
title: LinkedIn AI Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---
# LinkedIn AI Agent

An AI chatbot that answers questions about my professional background using Llama 3.3 via Groq.

## 🚀 Demo

🔗 [Try it live](https://huggingface.co/spaces/HalimehAgh/linkedin-agent)

## 🛠️ Tech Stack

- **Llama 3.3 70B** via Groq API
- **Gradio** for chat interface
- **PyPDF** for LinkedIn profile extraction

## ✨ Features

- Multi-turn conversations about my research and experience
- Answers based on actual LinkedIn profile and summary
- Fast inference using Groq's infrastructure

## 🔧 Quick Start
```bash
# Install dependencies
pip install groq python-dotenv pypdf gradio requests

# Set up .env file
echo "GROQ_API_KEY=your_key_here" > .env

# Add your LinkedIn PDF to me/linkedin.pdf
# Add your summary to me/summary.txt

# Run
python app.py
```

## 💡 Technical Notes

**Tool Calling**: The code includes function calling infrastructure (contact collection, question tracking) but it's currently disabled. Llama 3.3 shows inconsistent tool calling behavior compared to GPT-4/Claude. For production tool use, I'd recommend a hybrid approach with frontier models handling tool decisions.
