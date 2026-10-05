# Job Failure Escalator

A lightweight Python application that simplifies the process of escalating failed production jobs. It provides a local web interface for entering job details, selecting an on-call contact, and generating a pre-filled escalation email.

## Features

* **Job Escalation:** Capture job, scheme, runsheet, and shift details.
* **Email Generation:** Automatically generate an email with the appropriate subject, message, recipient, and CC list.
* **Email History:** Save up to 50 recently used on-call email addresses for quick access.
* **Input Validation:** Check required fields and email address formatting before generating an escalation.
* **Application Logging:** Record application activity and validation warnings locally.
* **Local Execution:** Runs in the default web browser using a local Flask server.

Emails are prepared in the user's default mail application for review and sending. The application does not send emails directly.

## Technologies Used

* Python
* Flask
* HTML/CSS
* python-dotenv
* JSON
* Python Logging

## Requirements

* Python 3.10+
* pip

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd Job-Failure-Escalator
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
OPERATORS_GROUP=
CSS_PROD=
```

Populate the variables with the appropriate email addresses for your environment. Keep your actual `.env` file out of version control.

## Running the Application

```bash
python main.py
```

The application opens in your default browser at:

`http://127.0.0.1:5000`

## Data and Logging

The application stores email history and logs locally under the user's application data directory:

```text
%APPDATA%\Job Failure Escalator\
├── email_history.json
└── logs\
    └── escalate.log
```

## Future Improvements

* Automated tests
* Improved input validation
* Additional email template options
* Windows executable packaging

## License

Available for educational and personal use.
