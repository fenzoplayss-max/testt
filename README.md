# AI Code Agent - Like Cursor AI

A powerful AI-powered coding assistant built with Python and Flask, similar to Cursor AI. It integrates with Google's Gemini API to provide intelligent code assistance, file operations, command execution, and more.

## Features

- **🤖 AI-Powered**: Uses Google Gemini API for intelligent responses
- **📁 File Operations**: Read, write, edit, create, and delete files and folders
- **💻 Command Execution**: Run shell commands and execute code
- **🧪 Testing & Debugging**: Test and debug your code automatically
- **🔍 File Explorer**: Browse and navigate your workspace
- **💬 Chat Interface**: Modern, responsive web UI
- **⚡ Real-time Actions**: See actions being performed in real-time

## Installation

### 1. Install Dependencies

```bash
pip install flask google-generativeai psutil
```

### 2. Get Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

### 3. Run the Server

```bash
python agent.py
```

The server will start at `http://localhost:5000`

## Usage

### Web Interface

1. Open your browser and go to `http://localhost:5000`
2. Type your request in the chat box
3. The AI will understand and execute actions to fulfill your request

### Example Requests

- "Create a Python script that calculates fibonacci numbers"
- "Build a simple Flask web application"
- "Read the file main.py and fix any bugs"
- "Create a React component for a todo list"
- "Run the tests in test_app.py"
- "Search for all Python files containing 'database'"

## API Endpoints

- `POST /api/chat` - Send a message to the AI
- `POST /api/reset` - Reset conversation history
- `GET /api/files/list?path=.` - List directory contents
- `POST /api/files/read` - Read a file
- `POST /api/files/write` - Write to a file
- `POST /api/command` - Execute a shell command
- `GET /api/status` - Get system status

## Project Structure

```
/workspace
├── agent.py              # Main backend application
├── templates/
│   └── index.html        # Web UI
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Available AI Actions

The AI can perform these actions automatically:

- `read_file` - Read file contents
- `write_file` - Create or overwrite a file
- `append_file` - Append content to a file
- `delete_file` - Delete a file
- `create_folder` - Create a new folder
- `delete_folder` - Delete a folder
- `list_directory` - List directory contents
- `search_files` - Search for files by pattern
- `execute_command` - Run shell commands
- `run_python` - Execute Python code

## Security Notes

- All file operations are restricted to the `/workspace` directory
- Commands run with the permissions of the user running the server
- Be cautious when running the server in production environments

## Troubleshooting

### API Key Not Working

Make sure you've set the `GEMINI_API_KEY` environment variable correctly:

```bash
echo $GEMINI_API_KEY  # Should show your API key
```

### Port Already in Use

If port 5000 is already in use, modify the last line in `agent.py`:

```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Change port to 5001
```

## License

MIT License - Feel free to use and modify!

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
