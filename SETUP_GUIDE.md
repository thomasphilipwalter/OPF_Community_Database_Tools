# OPFA Community Search - Setup Guide

## Quick Start (5 minutes)

### Prerequisites
- **Python 3.7+** installed on your computer
- **pip** (usually comes with Python)

### Installation Steps

1. **Extract the zip file** to a folder on your computer

2. **Open Terminal/Command Prompt** and navigate to the folder:
   ```bash
   cd path/to/Key_Word_App
   ```

3. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your web browser** and go to:
   ```
   http://localhost:5000
   ```

### Troubleshooting

**"python not found"**
- Install Python from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

**"pip not found"**
- Try: `python -m pip install -r requirements.txt`

**"port 5000 already in use"**
- Change the port in `app.py` line 95 to a different number like 5001
- Or stop other applications using port 5000

**"database not found"**
- Make sure `opfa_community.db` is in the same folder as `app.py`

### Features

- **Search** across all fields in the database
- **Export results** as CSV
- **Mobile responsive** design
- **Real-time search** with highlighting

### Usage

1. Enter any keyword or phrase in the search box
2. Click "Search" or press Enter
3. View results in formatted cards
4. Export results if needed

### Examples to try:
- Names: "Jared", "Shannon", "Alex"
- Companies: "Antea Group", "Persefoni"
- Skills: "sustainability", "consultant", "ESG"
- Locations: "Denver", "Chicago"

### Stopping the App

Press `Ctrl+C` in the terminal to stop the application.

---

**Need help?** Contact the person who sent you this app. 