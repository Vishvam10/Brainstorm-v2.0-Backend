# Brainstorm App

This is a flashcard application that will help you remember 
important things quikly. A demo link will be provided soon. But here's the link to Brainstorm v1.0 [Click here](https://brainstorm-flashcard-app.herokuapp.com/)

<br>

## Basic setup

Clone the project
```bash
  git clone 
```

Go to the project directory
```bash
  cd my-project
```

Create a virtual environment in the project folder

```bash
  python3 -m venv /path/to/new/virtual/environment
```

Install the dependencies using pip
```bash
  pip install - r requirements.txt
```

Run the development server 
```bash
  python main.py
```
<br>

**UNDER DEVELOPMENT - Jobs using Redis and Celery is not yet done**

<br>

Run the redis server - **UNDER DEVELOPMENT**
```bash
  redis-server
```
Run the celery server - **UNDER DEVELOPMENT**
```bash
  celery -A app.celery worker -l INFO
```
<br>
<br>

## API Documentation

**NOTE** : The link given below is for the initial API ( i.e. version 1 ). The version 2 is currently in development and version 2 has the additional APIs for auth, import, export and a couple other new features.

The API follows an OpenAPI 3.0.0 standard. [Click Here](./openapi.yaml) to view the full documentation in the YAML format. Paste it in Swagger Editor or any other OpenAPI tool to get a friendly-view

## Features

- [x] User Login / Signup
- [x] Authentication and Authorization using JWT  
- [x]  Personal Dashboard
- [x] Deck Management
- [x] Import and Export as Excel / CSV Jobs
- [x] Using webhooks for sending emails and SMS notifications and reminders
- [x] Card Management
- [x] Graphical Analysis
- [x] Revision Recommendations
- [x] Cross Platform


