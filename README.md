# Movie Recommender System CI/CD

## Overview
This project is a Movie Recommender System implemented with a CI/CD pipeline using Jenkins, GitHub, and AWS. It automates building, testing, and deploying the application whenever changes are pushed to the repository.

## Features
- Recommends movies based on user preferences.
- Automated CI/CD pipeline integrated with GitHub and AWS.
- Dockerized application for consistent deployment.

## Prerequisites
- Docker installed on the build environment.
- Jenkins server with Docker Pipeline, GitHub Integration, and AWS CodeDeploy plugins.
- AWS CLI configured with appropriate credentials.
- GitHub repository access.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git
   cd MovieRecommenderSystemCICD
   ```
2. **Build the Docker Image**:
   ```bash
   docker build -t movie-recommender:latest .
   ```
3. **Run the Application**:
   ```bash
   docker run -p 5000:5000 movie-recommender:latest
   ```

## CI/CD Pipeline
- **Jenkinsfile**: Defines stages for Checkout, Build, Test, and Deploy.
- **Trigger**: Automatically runs on push to the `main` branch via GitHub webhook.
- **Deployment**: Deploys to AWS using EC2 instance and CodeDeploy.

## Usage
- Access the application at `http://localhost:5000` (or your AWS endpoint after deployment).
- Update the `Jenkinsfile` or application code, push to GitHub, and monitor the pipeline in Jenkins.

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions, contact Mohamed Amine Affes at [your-email@example.com](mailto:your-email@example.com).