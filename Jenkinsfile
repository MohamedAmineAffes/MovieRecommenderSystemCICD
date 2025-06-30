pipeline {
    agent any

    environment {
        EC2_HOST = '16.171.35.98'                 // Your EC2 public IP
        EC2_CRED = credentials('ec2-ssh-key')    // Your Jenkins SSH credential
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git'
                sh 'ls -la'  // Debug: List files to confirm workspace contents
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo 'Building images with Docker Compose...'
                    sh 'docker-compose build'
                }
            }
        }

        stage('Run Application') {
            steps {
                script {
                    echo 'Launching app with Docker Compose...'

                    // Stop existing services if running
                    sh 'docker-compose down || true'

                    // Start services
                    sh 'docker-compose up -d'
                }
            }
        }


        stage('Test SSH Connection') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} "echo Successfully connected to EC2"
                    """
                }
            }
            post {
                failure {
                    error 'SSH to EC2 failed! Check credentials, IP, and security group settings.'
                }
            }
        }

        stage('Prepare EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} "mkdir -p ~/movie_recommender"
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    script {

                        echo 'Saving and compressing Docker image...'
                        sh 'docker save -o movie-recommender.tar movie-recommender:latest'
                        sh 'gzip movie-recommender.tar' // Compress the tar file

                        echo 'Ensuring remote directory exists...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'mkdir -p ~/movie_recommender'"

                        echo 'Copying compressed Docker image to EC2...'
                        sh "scp -o StrictHostKeyChecking=no movie-recommender.tar.gz ubuntu@${EC2_HOST}:~/movie_recommender/"

                        echo 'Decompressing Docker image on EC2...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'gunzip ~/movie_recommender/movie-recommender.tar.gz'"

                        echo 'Loading Docker image on EC2...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'docker load -i ~/movie_recommender/movie-recommender.tar'"

                        echo 'Stopping and removing existing container (if exists)...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'docker rm -f movie-recommender-container || true'"

                        echo 'Running Docker container on EC2...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'docker run -d --name movie-recommender-container -p 5000:5000 movie-recommender:latest'"

                        echo 'Cleaning up remote tar file...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'rm ~/movie_recommender/movie-recommender.tar'"

                        echo 'Cleaning up local compressed file...'
                        sh 'rm movie-recommender.tar.gz'
                    }
                }
            }
            post {
                success {
                    echo 'Docker container deployed successfully!'
                }
                failure {
                    echo 'Deployment to EC2 failed!'
                }
            }
        }



        stage('Run Tests Inside Container') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh ubuntu@${EC2_HOST} "docker exec movie-recommender-container pytest /app/script_stage.py -v"
                    """
                }
            }
            post {
                failure {
                    echo 'Tests failed inside Docker container on EC2!'
                }
            }
        }
    }
}
