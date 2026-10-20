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
            bat 'python -m pytest'
        }
    }
}

post {
    success {
        echo 'College Message pipeline completed successfully!'
    }

    failure {
        echo 'Build failed. Check the Console Output.'
    }
}