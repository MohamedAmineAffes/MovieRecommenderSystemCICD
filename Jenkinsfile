pipeline {
    agent any
    environment {
        EC2_HOST = '13.60.32.96'  // Your EC2 public IP
        EC2_CRED = credentials('ec2-ssh-key')  // Your Jenkins SSH credential
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git'
                sh 'ls -la ${WORKSPACE}'  // Debug: Verify workspace contents
            }
        }

        stage('Test SSH with Encrypted Key') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh 'ssh -o StrictHostKeyChecking=no ubuntu@"${EC2_HOST}" "echo Successfully connected"'
                }
            }
            post {
                failure {
                    error 'SSH to EC2 failed! Check credentials and network.'
                }
            }
        }






        stage('Build') {
            steps {
                script {
                    echo 'Building Docker image...'
                    dockerImage = docker.build("movie-recommender:latest")
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh '''
                        # Save the Docker image as a tar file locally
                        docker save -o movie-recommender.tar movie-recommender:latest
                        # Copy the tar file to EC2
                        scp movie-recommender.tar ubuntu@${EC2_HOST}:~/movie_recommender/
                        # Load and run the image on EC2
                        ssh ubuntu@${EC2_HOST} '
                            cd ~/movie_recommender &&
                            docker load -i movie-recommender.tar &&
                            docker rm -f movie-recommender-container || true &&
                            docker run -d --name movie-recommender-container -p 5000:5000 movie-recommender:latest &&
                            rm movie-recommender.tar
                        '
                        # Clean up local tar file
                        rm movie-recommender.tar
                    '''
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

        stage('Test on EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh '''
                        # Execute test inside the running container
                        ssh ubuntu@"${EC2_HOST}" <<EOF
                        docker exec movie-recommender-container bash -c ". /app/.venv/bin/activate && pytest /app/script_stage.py -v"
                        EOF
                    '''
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