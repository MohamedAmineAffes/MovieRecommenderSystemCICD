pipeline {
    agent any
    environment {
        EC2_HOST = '13.60.32.96'  // Replace with your EC2 instance's public IP or DNS
        EC2_CRED = credentials('ec2-ssh-key')  // Reference your SSH credential
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/MohamedAmineAffes/MovieRecommenderSystemCICD.git'
                sh 'ls -la ${WORKSPACE}'
            }
        }

        stage('Test SSH with Encrypted Key') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh 'ssh -o StrictHostKeyChecking=no ubuntu@"${EC2_HOST}" "echo Successfully connected with encrypted key"'
                }
            }
            post {
                failure {
                    error 'SSH connection to EC2 failed! Check credentials and network.'
                }
            }
        }

        stage('Setup on EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    // Step 1: Create directory and install python3-venv
                    sh 'ssh -o StrictHostKeyChecking=no ubuntu@"${EC2_HOST}" <<EOF\nmkdir -p ~/movie_recommender\nsudo apt update\nsudo apt install -y python3.10-venv -qq\nEOF'

                    // Step 2: Transfer files from workspace to EC2
                    sh 'if [ -d "${WORKSPACE}" ]; then scp -r ${WORKSPACE}/* ubuntu@"${EC2_HOST}":~/movie_recommender/; else echo "Workspace directory not found! Check Checkout stage."; exit 1; fi'

                    // Step 3: Set up virtual environment and install dependencies
                    sh 'ssh -o StrictHostKeyChecking=no ubuntu@"${EC2_HOST}" <<EOF\ncd ~/movie_recommender\npython3 -m venv .venv\n. .venv/bin/activate\npip install --upgrade pip\npip install -r requirements.txt\nEOF'
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

        stage('Test on EC2') {
            steps {
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no ubuntu@"${EC2_HOST}" <<EOF
                        cd ~/movie_recommender
                        . .venv/bin/activate
                        pytest script_stage.py -v
                        EOF
                    '''
                }
            }
            post {
                failure {
                    echo 'Tests failed on EC2!'
                }
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying Docker container to AWS EC2...'
                sshagent (credentials: ['ec2-ssh-key']) {
                    sh '''
                        # Save the Docker image as a tar file locally
                        docker save -o movie-recommender.tar movie-recommender:latest
                        # Copy the tar file to EC2
                        scp movie-recommender.tar ubuntu@"${EC2_HOST}":~/movie_recommender/
                        # Load and run the image on EC2
                        ssh ubuntu@"${EC2_HOST}" <<EOF
                        cd ~/movie_recommender
                        docker load -i movie-recommender.tar
                        # Stop and remove any existing container with the same name
                        docker rm -f movie-recommender-container || true
                        # Run the container (adjust port and command as per your Dockerfile)
                        docker run -d --name movie-recommender-container -p 5000:5000 movie-recommender:latest
                        rm movie-recommender.tar  # Clean up tar file
                        EOF
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
                    echo 'Deployment failed!'
                }
            }
        }
    }
}