node {
    stage('Checkout') {
        checkout scm
    }

    stage('Check Python') {
        bat 'python --version'
        bat 'python -m pip --version'
    }

    stage('Install Dependencies') {
        if (fileExists('requirements.txt')) {
            bat 'python -m pip install -r requirements.txt'
        } else {
            error 'requirements.txt is missing from the project root.'
        }
    }

    stage('Run Tests') {
        if (fileExists('tests') || fileExists('test_app.py')) {
            bat 'python -m pip install pytest'
            bat 'python -m pytest'
        } else {
            echo 'No recognized test directory or test_app.py found. Skipping tests.'
        }
    }

    stage('Complete') {
        echo 'College Message pipeline completed successfully!'
    }
}