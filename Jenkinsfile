node {
    stage('Checkout') {
        checkout scm
    }

    stage('Check Python') {
        sh 'python3 --version'
        sh 'python3 -m venv --help'
    }

    stage('Create Virtual Environment') {
        sh 'python3 -m venv .venv'
    }

    stage('Install Dependencies') {
        if (fileExists('requirements.txt')) {
            sh '.venv/bin/python -m pip install --upgrade pip'
            sh '.venv/bin/python -m pip install -r requirements.txt'
        } else {
            error 'requirements.txt is missing from the project root.'
        }
    }

    stage('Run Tests') {
        if (fileExists('tests') || fileExists('test_app.py')) {
            sh '.venv/bin/python -m pip install pytest'
            sh '.venv/bin/python -m pytest'
        } else {
            echo 'No recognized test directory or test_app.py found. Skipping tests.'
        }
    }

    stage('Complete') {
        echo 'College Message pipeline completed successfully!'
    }
}