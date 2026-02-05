# 🚀 Streamlit AI Chat Assistant

A feature-rich chatbot application built with Streamlit that interfaces with OpenAI models through OpenRouter. This application provides a clean, user-friendly interface for multi-conversation AI chat with customizable response styles.

## ✨ Features

- **Multi-Chat Management**: Create and manage multiple conversation threads
- **Customizable Response Styles**: Choose from 14 different AI response styles including Friendly, Professional, Technical, Creative, and more
- **Chat History**: Persistent chat sessions with automatic title generation
- **Configurable Settings**: Adjust chat history limits and display preferences
- **Session Statistics**: Track session duration, total chats, and message counts
- **Timestamps**: Optional message timestamps for tracking conversation flow
- **Clean UI**: Modern interface with custom CSS styling

## 📋 Prerequisites

- Python 3.7+
- OpenRouter API key
- Streamlit
- OpenAI Python library

## 🔧 Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Install required dependencies:
```bash
pip install streamlit openai requests
```

3. Create a `.streamlit/secrets.toml` file in your project directory:
```toml
OPENROUTER_API_KEY = "your-openrouter-api-key-here"
```

4. (Optional) Add your custom CSS file:
Create a `styles.css` file in the project root for custom styling.

## 🚀 Usage

Run the application with:
```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## 🎯 Key Features Explained

### Response Styles

Choose from 14 different response styles to customize how the AI responds:

- **Friendly**: Warm and approachable tone
- **Professional**: Formal, business-appropriate responses
- **Concise**: Brief, to-the-point answers
- **Verbose**: Detailed explanations with thorough reasoning
- **Technical**: Precise technical language for experienced users
- **Beginner-Friendly**: Simple explanations for newcomers
- **Direct**: Plain, no-filler responses
- **Analytical**: Logical, step-by-step breakdowns
- **Socratic**: Guided learning through questions
- **Critical**: Challenges assumptions and identifies edge cases
- **Creative**: Imaginative responses with metaphors
- **Neutral**: Factual, opinion-free answers
- **Persuasive**: Convincing arguments with logical reasoning
- **Action-Oriented**: Focus on concrete next steps

### Chat Management

- **New Chat**: Create unlimited conversation threads
- **Auto-Titles**: Conversations are automatically titled based on initial messages
- **Delete Chats**: Remove unwanted conversations
- **Chat Switching**: Seamlessly switch between different conversations

### Configuration Options

- **Assistant Name**: Customize the chatbot's display name
- **Response Style**: Select the AI's communication style
- **Max Chat History**: Control how many messages are displayed (5-100)
- **Show Timestamps**: Toggle message timestamps on/off

## 📁 Project Structure

```
.
├── app.py                  # Main application file
├── styles.css             # Custom CSS styling
├── .streamlit/
│   └── secrets.toml       # API keys (not tracked in git)
└── README.md              # This file
```

## 🔑 Environment Variables

The application requires the following secret to be configured in `.streamlit/secrets.toml`:

- `OPENROUTER_API_KEY`: Your OpenRouter API key for accessing AI models

## 🤖 Model Configuration

The app currently uses the `openai/gpt-oss-120b` model via OpenRouter. To change the model, modify the `MODEL_NAME` variable in `app.py`:

```python
MODEL_NAME = "your-preferred-model"
```

## 🛠 Development

### Future Enhancements

- [ ] Persistent chat storage (database or file-based)
- [ ] Streaming responses for real-time output
- [ ] LLM-based chat title generation
- [ ] Export chat history
- [ ] User authentication
- [ ] Message editing and regeneration
- [ ] Dark/light theme toggle

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenRouter](https://openrouter.ai/)
- Uses OpenAI's API interface

## ⚠️ Note

Remember to keep your API keys secure and never commit them to version control. Always use environment variables or Streamlit secrets for sensitive information.

## 📧 Support

For issues, questions, or suggestions, please open an issue in the GitHub repository.

---

**Happy Chatting! 🎉**