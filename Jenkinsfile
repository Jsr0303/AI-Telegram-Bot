pipeline {

    agent any

    environment {
        // --------------------------------------------------
        // These names on LEFT must match your code (config.py)
        // Values on RIGHT must match Jenkins Credential IDs
        // --------------------------------------------------
        BOT_TOKEN            = credentials('TELEGRAM_BOT_TOKEN')  // matches config.py BOT_TOKEN
        GEMINI_API_KEY       = credentials('GEMINI_API_KEY')       // matches config.py GEMINI_API_KEY
        BRAVE_SEARCH_API_KEY = credentials('BRAVE_API_KEY')        // matches config.py BRAVE_SEARCH_API_KEY
        MONGO_URI            = credentials('MONGODB_URI')          // matches config.py MONGO_URI
        VENV_DIR             = 'venv'
    }

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'production'],
            description: 'Which environment to deploy to?'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run tests before deploying?'
        )
        booleanParam(
            name: 'SKIP_DEPLOY',
            defaultValue: false,
            description: 'Skip deploy stage?'
        )
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        // ----------------------------------------
        // STAGE 1: CHECKOUT
        // Clone repo from GitHub into workspace
        // ----------------------------------------
        stage('Checkout') {
            steps {
                echo '====== Checking out source code from GitHub ======'
                checkout scm
                sh '''
                    echo "Repo cloned successfully"
                    echo "Workspace: $(pwd)"
                    ls -la
                    echo "Last Commit: $(git log -1 --oneline)"
                '''
            }
        }

        // ----------------------------------------
        // STAGE 2: ENVIRONMENT SETUP
        // Create Python virtual environment
        // ----------------------------------------
        stage('Environment Setup') {
            steps {
                echo '====== Setting up Python virtual environment ======'
                sh '''
                    python3 --version
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip --quiet
                    echo "Virtual environment ready!"
                '''
            }
        }

        // ----------------------------------------
        // STAGE 3: INSTALL DEPENDENCIES
        // Install all packages from requirements.txt
        // ----------------------------------------
        stage('Install Dependencies') {
            steps {
                echo '====== Installing Python dependencies ======'
                sh '''
                    echo "requirements.txt:"
                    cat requirements.txt
                    echo ""
                    . ${VENV_DIR}/bin/activate
                    pip install -r requirements.txt --quiet
                    echo "All packages installed!"
                    pip list
                '''
            }
        }

        // ----------------------------------------
        // STAGE 4: VALIDATE CONFIG
        // Check all secrets are present before deploy
        // Variable names match exactly what config.py uses
        // ----------------------------------------
        stage('Validate Config') {
            steps {
                echo '====== Validating secrets ======'
                sh '''
                    echo "Checking BOT_TOKEN..."
                    if [ -z "$BOT_TOKEN" ]; then
                        echo "BOT_TOKEN is MISSING!"
                        exit 1
                    else
                        echo "BOT_TOKEN is set"
                    fi

                    echo "Checking GEMINI_API_KEY..."
                    if [ -z "$GEMINI_API_KEY" ]; then
                        echo "GEMINI_API_KEY is MISSING!"
                        exit 1
                    else
                        echo "GEMINI_API_KEY is set"
                    fi

                    echo "Checking BRAVE_SEARCH_API_KEY..."
                    if [ -z "$BRAVE_SEARCH_API_KEY" ]; then
                        echo "BRAVE_SEARCH_API_KEY is MISSING!"
                        exit 1
                    else
                        echo "BRAVE_SEARCH_API_KEY is set"
                    fi

                    echo "Checking MONGO_URI..."
                    if [ -z "$MONGO_URI" ]; then
                        echo "MONGO_URI is MISSING!"
                        exit 1
                    else
                        echo "MONGO_URI is set"
                    fi

                    echo "All secrets present!"
                    echo "Deploy target: ${DEPLOY_ENV}"
                '''
            }
        }

        // ----------------------------------------
        // STAGE 5: DEPLOY
        // Start the bot with correct env variables
        // .env file uses same names as config.py
        // ----------------------------------------
        stage('Deploy') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo "====== Deploying to: ${params.DEPLOY_ENV} ======"
                sh '''
                    echo "Stopping any existing bot..."
                    pkill -f "python3 bot.py" || echo "No existing process"
                    sleep 2

                    echo "Writing .env file..."
                    cat > .env << ENVEOF
BOT_TOKEN=${BOT_TOKEN}
GEMINI_API_KEY=${GEMINI_API_KEY}
BRAVE_SEARCH_API_KEY=${BRAVE_SEARCH_API_KEY}
MONGO_URI=${MONGO_URI}
ENVEOF

                    echo ".env file created with correct variable names"

                    . ${VENV_DIR}/bin/activate
                    echo "Starting bot..."
                    nohup python3 bot.py > bot.log 2>&1 &
                    BOT_PID=$!
                    echo "Bot started with PID: $BOT_PID"

                    sleep 5
                    if kill -0 $BOT_PID 2>/dev/null; then
                        echo "Bot is RUNNING!"
                    else
                        echo "Bot crashed! Logs:"
                        cat bot.log
                        exit 1
                    fi
                '''
            }
        }

        // ----------------------------------------
        // STAGE 6: HEALTH CHECK
        // Verify bot is running after deploy
        // ----------------------------------------
        stage('Health Check') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo '====== Running health check ======'
                sh '''
                    . ${VENV_DIR}/bin/activate

                    if pgrep -f "python3 bot.py" > /dev/null; then
                        echo "Bot process is RUNNING"
                    else
                        echo "Bot process not found"
                    fi

                    echo "Checking Python imports..."
                    python3 - << PYCHECK
import sys
print(f"Python {sys.version}")
modules = {
    "telegram": "python-telegram-bot",
    "google.generativeai": "google-generativeai",
    "pymongo": "pymongo",
}
for mod, name in modules.items():
    try:
        __import__(mod)
        print(f"  OK: {name}")
    except ImportError as e:
        print(f"  MISSING: {name} - {e}")
PYCHECK
                    echo "Health check complete!"
                '''
            }
        }

    }

    post {
       
        success {
            echo 'BUILD SUCCEEDED - Bot is running!'
        }
        failure {
            echo 'BUILD FAILED - Check logs above'
        }
    }

}