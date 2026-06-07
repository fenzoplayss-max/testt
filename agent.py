"""
AI Agent Backend - Similar to Cursor AI
Features:
- Gemini API integration for AI responses
- File/folder operations (read, write, edit, create, delete)
- Command execution and code running
- Testing and debugging capabilities
- Full requirement fulfillment
"""

import os
import subprocess
import json
import re
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, stream_with_context
import psutil
import shutil
from datetime import datetime

app = Flask(__name__)

# Configuration - Use current directory on Windows, /workspace on Linux/Mac
if os.name == 'nt':  # Windows
    WORKSPACE_ROOT = os.getcwd()
else:
    WORKSPACE_ROOT = "/workspace"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Configure Gemini API (suppress deprecation warning for now)
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

class FileSystemTool:
    """Tool for file system operations"""
    
    def __init__(self, root_dir=WORKSPACE_ROOT):
        self.root_dir = root_dir
    
    def _safe_path(self, path):
        """Ensure path is within workspace root"""
        abs_path = os.path.abspath(os.path.join(self.root_dir, path))
        if not abs_path.startswith(self.root_dir):
            raise ValueError(f"Path {path} is outside workspace root")
        return abs_path
    
    def read_file(self, path):
        """Read contents of a file"""
        try:
            safe_path = self._safe_path(path)
            if not os.path.exists(safe_path):
                return {"error": f"File not found: {path}"}
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {"content": content, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def write_file(self, path, content):
        """Write content to a file"""
        try:
            safe_path = self._safe_path(path)
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path, "message": f"Successfully wrote to {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def append_file(self, path, content):
        """Append content to a file"""
        try:
            safe_path = self._safe_path(path)
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path, "message": f"Successfully appended to {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def delete_file(self, path):
        """Delete a file"""
        try:
            safe_path = self._safe_path(path)
            if os.path.exists(safe_path):
                os.remove(safe_path)
                return {"success": True, "path": path, "message": f"Successfully deleted {path}"}
            return {"error": f"File not found: {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def create_folder(self, path):
        """Create a folder"""
        try:
            safe_path = self._safe_path(path)
            os.makedirs(safe_path, exist_ok=True)
            return {"success": True, "path": path, "message": f"Successfully created folder {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def delete_folder(self, path):
        """Delete a folder and its contents"""
        try:
            safe_path = self._safe_path(path)
            if os.path.exists(safe_path) and os.path.isdir(safe_path):
                shutil.rmtree(safe_path)
                return {"success": True, "path": path, "message": f"Successfully deleted folder {path}"}
            return {"error": f"Folder not found: {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def list_directory(self, path="."):
        """List contents of a directory"""
        try:
            safe_path = self._safe_path(path)
            if not os.path.exists(safe_path):
                return {"error": f"Directory not found: {path}"}
            items = []
            for item in os.listdir(safe_path):
                item_path = os.path.join(safe_path, item)
                item_type = "folder" if os.path.isdir(item_path) else "file"
                items.append({"name": item, "type": item_type})
            return {"items": items, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def search_files(self, pattern, path="."):
        """Search for files matching a pattern"""
        try:
            safe_path = self._safe_path(path)
            matches = []
            for root, dirs, files in os.walk(safe_path):
                for file in files:
                    if re.search(pattern, file):
                        rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                        matches.append(rel_path)
            return {"matches": matches, "pattern": pattern}
        except Exception as e:
            return {"error": str(e)}


class CommandExecutor:
    """Tool for executing shell commands"""
    
    def __init__(self, working_dir=WORKSPACE_ROOT):
        self.working_dir = working_dir
    
    def execute(self, command, timeout=60):
        """Execute a shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}
    
    def run_python(self, code, timeout=30):
        """Run Python code"""
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Code execution timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}


class AIAgent:
    """Main AI Agent that orchestrates all tools"""
    
    def __init__(self):
        self.fs = FileSystemTool()
        self.cmd = CommandExecutor()
        self.conversation_history = []
    
    def get_system_prompt(self):
        """Get the system prompt for the AI agent"""
        return """You are an advanced AI coding assistant similar to Cursor AI. You have access to various tools to help users with their coding tasks.

Your capabilities include:
1. Reading, writing, editing, creating, and deleting files and folders
2. Executing shell commands
3. Running and testing code
4. Debugging issues
5. Understanding and implementing full project requirements

When you need to perform an action, respond with a JSON object in this format:
{
    "action": "action_name",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    }
}

Available actions:
- read_file: {"path": "relative/path/to/file"}
- write_file: {"path": "relative/path/to/file", "content": "file content"}
- append_file: {"path": "relative/path/to/file", "content": "content to append"}
- delete_file: {"path": "relative/path/to/file"}
- create_folder: {"path": "relative/path/to/folder"}
- delete_folder: {"path": "relative/path/to/folder"}
- list_directory: {"path": "relative/path"}
- search_files: {"pattern": "regex_pattern", "path": "relative/path"}
- execute_command: {"command": "shell command", "timeout": 60}
- run_python: {"code": "python code", "timeout": 30}

After performing an action, you will receive the result. Continue helping the user until their request is fully completed.

Always be helpful, thorough, and explain what you're doing. Work within the /workspace directory.

If the user's request is complete, respond with:
{"action": "complete", "message": "Summary of what was accomplished"}

For regular conversation or explanations, just respond with text (not JSON)."""

    def process_action(self, action_data):
        """Process an action from the AI and return the result"""
        action = action_data.get("action")
        params = action_data.get("parameters", {})
        
        if action == "read_file":
            return self.fs.read_file(params.get("path", ""))
        elif action == "write_file":
            return self.fs.write_file(params.get("path", ""), params.get("content", ""))
        elif action == "append_file":
            return self.fs.append_file(params.get("path", ""), params.get("content", ""))
        elif action == "delete_file":
            return self.fs.delete_file(params.get("path", ""))
        elif action == "create_folder":
            return self.fs.create_folder(params.get("path", ""))
        elif action == "delete_folder":
            return self.fs.delete_folder(params.get("path", ""))
        elif action == "list_directory":
            return self.fs.list_directory(params.get("path", "."))
        elif action == "search_files":
            return self.fs.search_files(params.get("pattern", ""), params.get("path", "."))
        elif action == "execute_command":
            return self.cmd.execute(params.get("command", ""), params.get("timeout", 60))
        elif action == "run_python":
            return self.cmd.run_python(params.get("code", ""), params.get("timeout", 30))
        elif action == "complete":
            return {"completed": True, "message": action_data.get("message", "")}
        else:
            return {"error": f"Unknown action: {action}"}
    
    def chat(self, user_message):
        """Process a user message and return AI response with tool execution"""
        if not model:
            return {"error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."}
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "parts": [user_message]})
        
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Prepare messages for Gemini
            messages = [{"role": "user", "parts": [self.get_system_prompt()]}]
            messages.extend(self.conversation_history)
            
            # Get AI response
            try:
                response = model.generate_content(messages)
                response_text = response.text.strip()
            except Exception as e:
                error_msg = str(e)
                if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    return {
                        "error": "API quota exceeded. Please wait ~25 seconds and try again, or check your Gemini API billing settings.",
                        "completed": False,
                        "actions_taken": 0,
                        "retry_after": 25
                    }
                raise
            
            # Try to parse as JSON action
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    action_data = json.loads(json_match.group())
                    
                    # Check if it's a completion action
                    if action_data.get("action") == "complete":
                        result = self.process_action(action_data)
                        self.conversation_history.append({"role": "model", "parts": [response_text]})
                        return {"response": result.get("message", "Task completed"), "completed": True, "actions_taken": iteration}
                    
                    # Execute the action
                    result = self.process_action(action_data)
                    
                    # Add action result to conversation
                    self.conversation_history.append({
                        "role": "model", 
                        "parts": [f"I will perform this action: {json.dumps(action_data)}"]
                    })
                    self.conversation_history.append({
                        "role": "user",
                        "parts": [f"Action result: {json.dumps(result)}"]
                    })
                    
                    # Continue loop to process next action
                    continue
                else:
                    # Regular text response
                    self.conversation_history.append({"role": "model", "parts": [response_text]})
                    return {"response": response_text, "completed": False, "actions_taken": iteration}
            except json.JSONDecodeError:
                # Not a JSON response, return as text
                self.conversation_history.append({"role": "model", "parts": [response_text]})
                return {"response": response_text, "completed": False, "actions_taken": iteration}
        
        return {"response": "Maximum iterations reached. Please provide more specific instructions.", "completed": False, "actions_taken": iteration}
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history = []


# Global agent instance
agent = AIAgent()


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    result = agent.chat(user_message)
    return jsonify(result)


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation"""
    agent.reset()
    return jsonify({"success": True, "message": "Conversation reset"})


@app.route('/api/files/list', methods=['GET'])
def list_files():
    """List files in a directory"""
    path = request.args.get('path', '.')
    result = agent.fs.list_directory(path)
    return jsonify(result)


@app.route('/api/files/read', methods=['POST'])
def read_file():
    """Read a file"""
    data = request.json
    path = data.get('path', '')
    result = agent.fs.read_file(path)
    return jsonify(result)


@app.route('/api/files/write', methods=['POST'])
def write_file():
    """Write to a file"""
    data = request.json
    path = data.get('path', '')
    content = data.get('content', '')
    result = agent.fs.write_file(path, content)
    return jsonify(result)


@app.route('/api/command', methods=['POST'])
def execute_command():
    """Execute a command"""
    data = request.json
    command = data.get('command', '')
    timeout = data.get('timeout', 60)
    result = agent.cmd.execute(command, timeout)
    return jsonify(result)


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        disk_usage = psutil.disk_usage(WORKSPACE_ROOT).percent
    except FileNotFoundError:
        # Fallback for Windows or invalid paths
        disk_usage = psutil.disk_usage(os.getcwd()).percent
    
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": disk_usage,
        "workspace": WORKSPACE_ROOT,
        "api_configured": bool(GEMINI_API_KEY)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("AI Agent Server Starting...")
    print(f"Workspace Root: {WORKSPACE_ROOT}")
    print(f"Gemini API Configured: {bool(GEMINI_API_KEY)}")
    if not GEMINI_API_KEY:
        print("\n⚠️  WARNING: GEMINI_API_KEY not set!")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
