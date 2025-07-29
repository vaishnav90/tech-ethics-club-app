# Tech & Ethics Club Website

A Flask-based website showcasing the Tech & Ethics Club with interactive 3D robot models and Python code animations.

## Features

- Interactive 3D robot models using Three.js
- Python code execution animation
- Responsive blueprint-themed design
- Multiple robot showcases
- Proper Creative Commons attribution

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
club2/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── models/           # 3D model files (.glb)
        ├── Robot Playground.glb
        ├── Autonomous Robot Sweeper.glb
        ├── Mini Robot Walk Cycle Test.glb
        ├── Cute Home Robot.glb
        └── Small Robot.glb
```

## 3D Model Credits

All 3D models are used under Creative Commons Attribution 4.0 license:
- Robot Playground by Hadrien59
- Autonomous Robot Sweeper by Janis Zeps
- Cute Home Robot by Yandrack
- Small Robot by TitMit

## Development

The application runs in debug mode by default. For production deployment, set `debug=False` in `app.py`. 