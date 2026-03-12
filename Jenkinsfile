pipeline {

    agent any

    environment {
        BOT_TOKEN            = credentials('TELEGRAM_BOT_TOKEN')
        GEMINI_API_KEY       = credentials('GEMINI_API_KEY')
        BRAVE_SEARCH_API_KEY = credentials('BRAVE_API_KEY')
        MONGO_URI            = credentials('MONGODB_URI')
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
        // ----------------------------------------
        stage('Install Dependencies') {
            steps {
                echo '====== Installing Python dependencies ======'
                sh '''
                    echo "requirements.txt:"
                    cat requirements.txt
                    . ${VENV_DIR}/bin/activate
                    pip install -r requirements.txt --quiet
                    echo "All packages installed!"
                '''
            }
        }

        // ----------------------------------------
        // STAGE 4: VALIDATE CONFIG
        // ----------------------------------------
        stage('Validate Config') {
            steps {
                echo '====== Validating secrets ======'
                sh '''
                    if [ -z "$BOT_TOKEN" ]; then
                        echo "BOT_TOKEN is MISSING!"
                        exit 1
                    else
                        echo "BOT_TOKEN is set"
                    fi

                    if [ -z "$GEMINI_API_KEY" ]; then
                        echo "GEMINI_API_KEY is MISSING!"
                        exit 1
                    else
                        echo "GEMINI_API_KEY is set"
                    fi

                    if [ -z "$BRAVE_SEARCH_API_KEY" ]; then
                        echo "BRAVE_SEARCH_API_KEY is MISSING!"
                        exit 1
                    else
                        echo "BRAVE_SEARCH_API_KEY is set"
                    fi

                    if [ -z "$MONGO_URI" ]; then
                        echo "MONGO_URI is MISSING!"
                        exit 1
                    else
                        echo "MONGO_URI is set"
                    fi

                    echo "All secrets present!"
                '''
            }
        }

        // ----------------------------------------
        // STAGE 5: DEPLOY
        // FIX 1: Write .env BEFORE activating venv
        // FIX 2: Show bot.log contents always
        // FIX 3: Longer wait time (8s not 5s)
        // FIX 4: Verify .env was written correctly
        // ----------------------------------------
        stage('Deploy') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo "====== Deploying to: ${params.DEPLOY_ENV} ======"
                sh """
                    echo "Stopping any existing bot..."
                    pkill -f "python3 bot.py" || echo "No existing process"
                    sleep 2

                    echo "Writing .env file..."
                    printf 'BOT_TOKEN=%s\nGEMINI_API_KEY=%s\nBRAVE_SEARCH_API_KEY=%s\nMONGO_URI=%s\n' \
                        '${BOT_TOKEN}' \
                        '${GEMINI_API_KEY}' \
                        '${BRAVE_SEARCH_API_KEY}' \
                        '${MONGO_URI}' > .env

                    echo ".env file written!"
                    echo "Lines in .env: \$(wc -l < .env)"

                    if [ ! -f .env ]; then
                        echo ".env file MISSING - cannot start bot!"
                        exit 1
                    fi

                    echo "Activating venv..."
                    . ${VENV_DIR}/bin/activate

                    echo "Starting bot in background..."
                    nohup python3 bot.py > bot.log 2>&1 &
                    BOT_PID=\$!
                    echo "Bot PID: \$BOT_PID"

                    echo "Waiting 10 seconds for bot to initialize..."
                    sleep 10

                    echo "=== BOT.LOG CONTENTS ==="
                    cat bot.log
                    echo "========================"

                    if kill -0 \$BOT_PID 2>/dev/null; then
                        echo "Bot is RUNNING successfully!"
                    else
                        echo "Bot CRASHED after startup!"
                        echo "Full bot.log:"
                        cat bot.log
                        exit 1
                    fi
                """
            }
        }

        // ----------------------------------------
        // STAGE 6: HEALTH CHECK
        // FIX 5: Check google.genai not generativeai
        // FIX 6: Show bot.log after health check
        // ----------------------------------------
        stage('Health Check') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo '====== Running health check ======'
                sh '''
                    . ${VENV_DIR}/bin/activate

                    echo "Checking bot process..."
                    if pgrep -f "python3 bot.py" > /dev/null; then
                        echo "Bot process is RUNNING"
                    else
                        echo "Bot process NOT FOUND - crashed!"
                        echo "=== BOT LOG ==="
                        cat bot.log
                        echo "==============="
                        exit 1
                    fi

                    echo ""
                    echo "Checking Python imports..."
                    python3 - << PYCHECK
import sys
print(f"Python {sys.version}")
modules = {
    "telegram":          "python-telegram-bot",
    "google.genai":      "google-genai",
    "pymongo":           "pymongo",
    "transformers":      "transformers",
    "dotenv":            "python-dotenv",
}
all_ok = True
for mod, name in modules.items():
    try:
        __import__(mod)
        print(f"  OK: {name}")
    except ImportError as e:
        print(f"  MISSING: {name} -> {e}")
        all_ok = False
if all_ok:
    print("All imports OK!")
else:
    print("Some imports FAILED!")
PYCHECK

                    echo ""
                    echo "=== FINAL BOT LOG ==="
                    cat bot.log
                    echo "====================="

                    echo "Health check complete!"
                '''
            }
        }

    }

    post {
        success {
            echo '======================================'
            echo 'BUILD SUCCEEDED - Bot is running!'
            echo 'Open Telegram and message your bot!'
            echo '======================================'
        }
        failure {
            echo '======================================'
            echo 'BUILD FAILED - Check logs above'
            echo '======================================'
        }
        always {
            echo "Job: ${env.JOB_NAME} | Build: #${env.BUILD_NUMBER} | Result: ${currentBuild.currentResult}"
        }
    }

}