pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git'
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
                    pytest script_stage.py -v  # Run tests with verbose output
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
