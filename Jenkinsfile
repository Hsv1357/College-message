```groovy
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Python') {
            steps {
                bat 'python --version'
                bat 'python -m pip --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    if (fileExists('tests')) {
                        bat 'python -m pytest tests'
                    } else if (fileExists('test_app.py')) {
                        bat 'python -m pytest test_app.py'
                    } else {
                        echo 'No recognized test directory or test_app.py found. Add automated tests to enable this stage.'
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Python CI pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check the Console Output for details.'
        }
    }
}
```