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
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying to AWS...'
            }
        }
    }
}
