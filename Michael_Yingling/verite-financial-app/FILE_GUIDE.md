# 📁 Vérité Financial - File Structure Guide

All files are now in one directory for easy access!

## 🎯 Quick Start Files

### **To See the Beautiful Design Immediately:**
- **`demo_preview.html`** - Open this in your browser right now! No setup needed.

### **To Run the Full Application:**
1. `requirements.txt` - Install dependencies: `pip install -r requirements.txt`
2. Set API key: `export ANTHROPIC_API_KEY='your-key-here'`
3. `web_app.py` - Run the web server: `python web_app.py`
4. Open browser to `http://localhost:5000`

### **To Run Command Line Demo:**
- `financial_advisor_app.py` - Run: `python financial_advisor_app.py`

### **To See Code Examples:**
- `example_usage.py` - Run: `python example_usage.py`

## 📋 Complete File List

### **Core Application Files**
- `financial_advisor_app.py` - Multi-agent orchestration engine (main logic)
- `web_app.py` - Flask web application (server)
- `config.py` - Configuration settings (customize here)

### **Frontend Files** (Used by Flask app)
- `index_template.html` - Main web interface template
- `styles.css` - Beautiful CSS styling
- `app.js` - Frontend JavaScript logic

### **Standalone Demo**
- `demo_preview.html` - Standalone preview (no server needed!)

### **Utility Scripts**
- `setup.py` - Quick setup and installation helper
- `example_usage.py` - Code usage examples

### **Documentation**
- `README.md` - Complete documentation
- `PROJECT_OVERVIEW.md` - Technical architecture details
- `FILE_GUIDE.md` - This file!

### **Dependencies**
- `requirements.txt` - Python package requirements

## 🚀 Recommended Workflow

**First Time:**
1. Open `demo_preview.html` to see the gorgeous design
2. Read `README.md` for detailed setup instructions
3. Run `python setup.py` for guided setup
4. Run `python web_app.py` to start the application

**Development:**
- Modify `config.py` to customize behavior
- Edit `styles.css` to change appearance
- Update `financial_advisor_app.py` to add new agents

## 📂 Original Directory Structure

The files are also organized in subdirectories:
```
├── financial_advisor_app.py
├── web_app.py
├── config.py
├── setup.py
├── example_usage.py
├── requirements.txt
├── README.md
├── PROJECT_OVERVIEW.md
│
├── templates/
│   └── index.html          (same as index_template.html)
│
└── static/
    ├── css/
    │   └── styles.css      (same as styles.css)
    └── js/
        └── app.js          (same as app.js)
```

Both structures work! Use whichever you prefer.

## 💡 Pro Tips

1. **For Flask to work**, it needs the `templates/` and `static/` folders
2. **For quick preview**, just use `demo_preview.html`
3. **To customize**, edit files in the root directory
4. **Clear browser cache** with Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

## 🎨 Design Features

Your app now has:
- ✨ Luxury gold & rose-gold gradients
- 🌌 Animated midnight blue background  
- 💎 Glassmorphic frosted glass cards
- 🎨 Elegant Cormorant Garamond serif font
- 💫 Smooth animations throughout

Enjoy your beautiful financial advisor app! 🚀
