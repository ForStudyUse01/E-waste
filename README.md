# E-Cycle AI - Smart E-Waste Management Platform

A Flask-based web application for managing electronic waste through AI-powered recognition and blockchain tracking.

## Features

- AI-powered e-waste recognition
- Recycling center locator
- Points-based rewards system
- Blockchain tracking
- Interactive user interface

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your secret key:
```
FLASK_SECRET_KEY=your_secret_key_here
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
e_waste/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── static/            # Static files (CSS, JS, images)
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── index.html     # Home page
    ├── scan.html      # E-waste scanning page
    ├── centers.html   # Recycling centers page
    ├── rewards.html   # Rewards page
    └── about.html     # About page
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 