# AWS Capstone Project

This project is a Flask-based web application designed for deployment on AWS. It allows users to browse projects, enroll in them, and administrators to manage the project portfolio. It leverages AWS services like DynamoDB for data storage and SNS for notifications.

## Features
- **User Portal**: Signup, Login, Browse Projects, Enroll in Projects.
- **Admin Portal**: Admin Signup/Login, Create Projects (with file uploads), Admin Dashboard.
- **AWS Integration**:
  - **DynamoDB**: Stores Users, Admins, Projects, and Enrollment data.
  - **SNS**: Sends notifications for activities like Signup and Enrollment.

## Prerequisites
- Python 3.8+
- AWS Account (for production deployment)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd aws_capstone_project_deployment
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally

### 1. Minimal Local Version
If you want to run the simple local version (no AWS dependencies):
```bash
python app.py
```

### 2. AWS Version (with Mocked Services)
To run the full **AWS-integrated app** locally without connecting to real AWS (using `moto` to simulate DynamoDB/SNS):
```bash
python test_app_aws.py
```
- Access the app at `http://localhost:5000`
- **Note**: Data is stored in memory and resets when the server stops.

## Deployment to AWS
To deploy to AWS EC2:
1. Provision an EC2 instance with an IAM Role containing `AmazonDynamoDBFullAccess` and `AmazonSNSFullAccess`.
2. Clone the code onto the instance.
3. Update `REGION` and `SNS_TOPIC_ARN` in `app_aws.py` if necessary.
4. Run the application:
   ```bash
   python app_aws.py
   ```
   *(For production, use `gunicorn` or a similar WSGI server).*

## Project Structure
- `app.py`: Simple local version (in-memory storage).
- `app_aws.py`: Main application for AWS deployment (DynamoDB/SNS).
- `test_app_aws.py`: Script to run `app_aws.py` locally with mocked AWS services.
- `templates/`: HTML templates.
- `static/`: CSS and static assets.
