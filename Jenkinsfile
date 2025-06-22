pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git'
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test SSH with Encrypted Key') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh 'ssh -o StrictHostKeyChecking=no ubuntu@13.60.32.96 "echo Successfully connected with encrypted key"'
                }
            }
        }


        stage('Build') {
            steps {
                script {
                    echo 'Building Docker image using Dockerfile...'
                    dockerImage = docker.build("movie-recommender:latest")
                }
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'
                // Run pytest in the virtual environment
                sh '''
                    . .venv/bin/activate # Activate the virtual environment
                    pytest script_stage.py
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying to AWS...'
            }
        }
    }
}
