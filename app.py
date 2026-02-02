from dotenv import load_dotenv
from groq import Groq
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

# Load environment variables
load_dotenv()

# Pushover notification function
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

# Tool functions
def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"New contact: {name} with email {email}. Notes: {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Unknown question: {question}")
    return {"recorded": "ok"}

# Tool definitions for the LLM
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# List of all tools
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

# Main class
class Me:
    def __init__(self):
        # Initialize Groq client
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.name = "Halimeh"
        
        # Load LinkedIn PDF
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        
        # Load summary
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        print(f"✅ Loaded LinkedIn PDF ({len(self.linkedin)} characters)")
        print(f"✅ Loaded summary ({len(self.summary)} characters)")

    def handle_tool_call(self, tool_calls):
        """Execute the tools that the LLM wants to call"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"\n⚠️  TOOL CALLED: {tool_name}")
            print(f"📝 Arguments: {arguments}\n", flush=True)
            
            # Call the actual function
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results
    
    def system_prompt(self):
        """Generate the system prompt with context about you"""
        prompt = f"""You are acting as {self.name}, answering questions about their professional background.

    CRITICAL RULES:
    1. ONLY use information from the Summary and LinkedIn Profile provided below
    2. If information is not in these documents, say "I don't have that specific information in my profile" - do NOT make up details
    3. ONLY use record_unknown_question tool if you genuinely cannot answer from the provided context
    4. ONLY use record_user_details tool when the user explicitly provides their email address
    5. Do NOT use tools preemptively or unnecessarily
    6. Be honest about what you know and don't know

    If asked about specific projects or experiences not mentioned in the documents, acknowledge what IS mentioned and clarify what isn't specified rather than inventing details.

    ## Summary:
    {self.summary}

    ## LinkedIn Profile:
    {self.linkedin}

    Stay strictly within this context when answering as {self.name}."""
    
        return prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}]
        
        # Convert Gradio's history format to simple role/content format
        for msg in history:
            if isinstance(msg, dict):
                # If it's already a dict, extract only role and content
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                # If it's [user_msg, assistant_msg] format from older Gradio
                messages.append({"role": "user", "content": msg[0]})
                if msg[1]:  # Only add if assistant responded
                    messages.append({"role": "assistant", "content": msg[1]})
        
        messages.append({"role": "user", "content": message})
        
        done = False
        max_iterations = 5  
        iteration = 0
        
        while not done and iteration < max_iterations:
            iteration += 1
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                #tools=tools,
                temperature=0.7,
                max_tokens=1024
            )
            
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "tool_calls":
                message_with_tools = response.choices[0].message
                tool_calls = message_with_tools.tool_calls
                results = self.handle_tool_call(tool_calls)
                
                messages.append({
                    "role": "assistant",
                    "content": message_with_tools.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                })
                messages.extend(results)
            else:
                done = True
        
        return response.choices[0].message.content



if __name__ == "__main__":
    me = Me()
    demo = gr.ChatInterface(
        me.chat,
        title="Chat with Halimeh - AI/ML Researcher",
        description="Ask me about my research, experience, and projects in AI for Software Engineering!"
    )
    demo.launch(share=False)