pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'farahcherif1'
        IMAGE_NAME     = "${DOCKERHUB_USER}/counter-app"
        // Identifiants Jenkins de type "Username with password" (voir guide)
        DOCKERHUB_CREDS = credentials('dockerhub-credentials')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    // Déclenchement automatique à chaque commit :
    //  - githubPush : webhook GitHub (réponse immédiate)
    //  - pollSCM    : filet de sécurité, Jenkins interroge le dépôt toutes les ~2 min
    triggers {
        githubPush()
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build & tests unitaires') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements.txt -r requirements-dev.txt
                    pytest -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        stage('Build de l\'image Docker') {
            steps {
                sh '''
                    docker build \
                        -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                        -t ${IMAGE_NAME}:${GIT_SHORT} \
                        -t ${IMAGE_NAME}:latest .
                    docker images ${IMAGE_NAME}
                '''
            }
        }

        stage('Publication sur Docker Hub') {
            steps {
                sh '''
                    echo "$DOCKERHUB_CREDS_PSW" | docker login -u "$DOCKERHUB_CREDS_USR" --password-stdin
                    docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                    docker push ${IMAGE_NAME}:${GIT_SHORT}
                    docker push ${IMAGE_NAME}:latest
                '''
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
            sh 'docker image prune -f || true'
        }
        success {
            echo "Image publiée : https://hub.docker.com/r/${IMAGE_NAME}"
        }
        failure {
            echo 'Pipeline en échec : consulter la Console Output.'
        }
    }
}
