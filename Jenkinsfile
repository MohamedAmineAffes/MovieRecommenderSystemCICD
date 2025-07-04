pipeline {
    agent any

    environment {
        EC2_HOST = '13.60.167.155'                 // Your EC2 public IP
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
                        echo 'Verifying if movie-recommender:latest Docker image exists...'
                        sh '''
                            set -e
                            IMAGE_CHECK=$(docker images -q movie-recommender:latest)

                            if [ -z "$IMAGE_CHECK" ]; then
                                echo "❌ ERROR: Docker image 'movie-recommender:latest' not found!"
                                echo "💡 Make sure to build the image before this deploy step."
                                exit 1
                            else
                                echo "✅ Docker image found: $IMAGE_CHECK"
                            fi
                        '''

                        echo 'Saving and compressing Docker image locally...'
                        // Save and compress in one step for better speed and less disk usage
                        sh 'docker save movie-recommender:latest | gzip > movie-recommender.tar.gz'

                        // ADD CHECK AFTER SAVE
                        echo 'Checking compressed file size...'
                        sh 'ls -lh movie-recommender.tar.gz'

                        echo 'Ensuring remote directory exists and cleaning old files...'
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                                mkdir -p ~/movie_recommender &&
                                rm -f ~/movie_recommender/movie-recommender.tar &&
                                rm -f ~/movie_recommender/movie-recommender.tar.gz
                            '
                        """

                        echo 'Copying compressed Docker image to EC2...'
                        sh "scp -o StrictHostKeyChecking=no movie-recommender.tar.gz ubuntu@${EC2_HOST}:~/movie_recommender/"

                        echo 'Decompressing and loading Docker image on EC2...'
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                                gunzip -c ~/movie_recommender/movie-recommender.tar.gz > ~/movie_recommender/movie-recommender.tar &&
                                docker load -i ~/movie_recommender/movie-recommender.tar
                            '
                        """

                        echo 'Stopping and removing existing container (if exists)...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'docker rm -f movie-recommender-container || true'"

                        echo 'Running Docker container on EC2... '
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'docker run -d --memory=300m --memory-swap=600m --name movie-recommender-container -p 5000:5000 movie-recommender:latest'
                        """

                        echo 'Cleaning up remote tar files...'
                        sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'rm -f ~/movie_recommender/movie-recommender.tar ~/movie_recommender/movie-recommender.tar.gz'"

                        echo 'Cleaning up local compressed file...'
                        sh 'rm -f movie-recommender.tar.gz'
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

    }
}
