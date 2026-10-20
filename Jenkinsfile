node {
    stage('Checkout') {
        checkout scm
    }

    stage('Check Python') {
        sh 'python3 --version'
        sh 'python3 -m pip --version'
    }

    stage('Install Dependencies') {
        if (fileExists('requirements.txt')) {
            sh 'python3 -m pip install -r requirements.txt'
        } else {
            error 'requirements.txt is missing from the project root.'
        }
    }

    stage('Run Tests') {
        if (fileExists('tests') || fileExists('test_app.py')) {
            sh 'python3 -m pip install pytest'
            sh 'python3 -m pytest'
        } else {
            echo 'No recognized test directory or test_app.py found. Skipping tests.'
        }
    }

    stage('Complete') {
        echo 'College Message pipeline completed successfully!'
    }
}