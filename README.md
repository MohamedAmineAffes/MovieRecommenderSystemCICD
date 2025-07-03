# 🎮 Movie Recommender System with CI/CD Pipeline

This project implements a **Movie Recommender System** with a complete **CI/CD pipeline** using **Jenkins**, **GitHub**, **Docker**, and **AWS EC2**. The pipeline automates building, testing, and deploying the application whenever changes are pushed to the repository.

---

## 🚀 Features

✅ Movie recommendations based on user preferences\
✅ Fully automated CI/CD pipeline with Jenkins\
✅ Integrated with GitHub Webhooks for automatic triggers\
✅ Dockerized for consistent and reliable deployment\
✅ Deployed to AWS EC2 using CodeDeploy

---

## 📦 Prerequisites

- Docker installed on your local machine or build server
- Jenkins server with the following plugins:
  - **Pipeline**
  - **Git Plugin**
  - **Docker Pipeline**
  - **SSH Agent Plugin**
  - **Credentials Plugin**
  - **SSH Credentials Plugin**
  - **Docker Commons Plugin**
  - **Durable Task Plugin**
- AWS CLI configured with valid credentials
- GitHub repository access

---

## 🛠️ Installation

### Clone the Repository

```bash
git clone https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git
cd MovieRecommenderSystemCICD
```

### Build the Docker Image

```bash
docker build -t movie-recommender:latest .
```

### Run the Application Locally

```bash
docker run -p 5000:5000 movie-recommender:latest
```

Visit the application at: [http://localhost:5000](http://localhost:5000)

---

## 🔄 CI/CD Pipeline Overview

- **Jenkinsfile** defines the pipeline stages:

  - ✅ Checkout source code
  - ✅ Build Docker image
  - ✅ Run tests
  - ✅ Deploy to AWS EC2 using CodeDeploy

- **Trigger:** Automatically triggered on push to the `main` branch via GitHub Webhook

- **Deployment:** Uses EC2 and AWS CodeDeploy for production deployment

---

## 🌐 Exposing Jenkins to GitHub (Local Setup)

If Jenkins is running locally, expose it using `ngrok`:

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
ngrok http 8080
```

Add the Webhook in your GitHub repository:\
**Settings → Webhooks → Add Webhook**

- **Payload URL:** `https://<ngrok-url>/github-webhook/`
- **Content type:** `application/json`
- **Events:** Just push events

---

## 🔑 Adding EC2 SSH Key to Jenkins

1. Copy your EC2 private key:

```bash
cat key-ec2.pem
```

2. In Jenkins:

- Go to **Manage Jenkins → Credentials → Global → Add Credentials**
- Select **SSH Username with private key**
- Paste your private key and save

---

## ✨ Usage

- Access the app at [http://localhost:5000](http://localhost:5000) or your AWS EC2 endpoint
- Push code changes to GitHub → Pipeline triggers → App redeployed automatically

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push the branch:
   ```bash
   git push origin feature-branch
   ```
5. Open a Pull Request

---

## 📬 Contact

For questions or support, contact:\
**Mohamed Amine Affes**\
📧 [mohamedamineaaffes@gmail.com](mailto\:mohamedamineaaffes@gmail.com)

---



