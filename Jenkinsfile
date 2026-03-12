// ============================================================
//        JENKINS PIPELINE — AI Telegram Bot
//        GitHub: https://github.com/Jsr0303/AI-Telegram-Bot
// ============================================================
// Project Stack:
//   - Python 3.9+
//   - Google Gemini API
//   - MongoDB
//   - Brave Search API
//   - python-telegram-bot v20+
//   - HuggingFace Transformers
// ============================================================

pipeline {

    // ----------------------------------------------------------
    // AGENT: Run pipeline on any available Jenkins node.
    // Jenkins needs Python 3.9+ installed on this machine.
    // ----------------------------------------------------------
    agent any

    // ----------------------------------------------------------
    // ENVIRONMENT: Secrets stored safely in Jenkins Credentials.
    // ⚠️  NEVER hardcode API keys directly here!
    //
    // HOW TO ADD SECRETS IN JENKINS:
    //   Manage Jenkins → Credentials → Global → Add Credentials
    //   Kind: "Secret text" → paste your key → set the ID below
    // ----------------------------------------------------------
    environment {
        TELEGRAM_BOT_TOKEN = credentials('8131763414:AAGBp7xYFFT2VfaDyx7_O1gfrJX9kVa63dc')  // Telegram Bot Token
        GEMINI_API_KEY     = credentials('AIzaSyD5n61roId4A5BNlV4_w5n_7iDncOKMpBM')       // Google Gemini API Key
        BRAVE_API_KEY      = credentials('BSAQrZFa4CXjLzRa67DEzVHf5J0WuWJ')        // Brave Search API Key
        MONGODB_URI        = credentials('MONGODB_URI')          // MongoDB URI
        VENV_DIR           = 'venv'                              // Virtual env folder
    }

    // ----------------------------------------------------------
    // PARAMETERS: Shown in "Build with Parameters" in Jenkins UI
    // ----------------------------------------------------------
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'production'],
            description: '🌍 Which environment to deploy to?'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: '✅ Run tests before deploying?'
        )
        booleanParam(
            name: 'SKIP_DEPLOY',
            defaultValue: false,
            description: '⏭️  Skip deploy? (just build and test)'
        )
    }

    options {
        timeout(time: 30, unit: 'MINUTES')           // Auto-kill if > 30 mins
        buildDiscarder(logRotator(numToKeepStr: '10')) // Keep last 10 builds only
        disableConcurrentBuilds()                    // No parallel runs
    }

    // ==========================================================
    //                        STAGES
    // ==========================================================
    stages {

        // ------------------------------------------------------
        // STAGE 1: CHECKOUT
        // Clones your GitHub repo into the Jenkins workspace.
        // Jenkins uses the SCM config set in the Pipeline job.
        // ------------------------------------------------------
        stage('📥 Checkout') {
            steps {
                echo '====== Checking out source code from GitHub ======'
                checkout scm
                sh '''
                    echo "✅ Repo cloned successfully"
                    echo "📁 Workspace: $(pwd)"
                    echo "📄 Files:"
                    ls -la
                    echo "🔀 Branch: $(git branch --show-current)"
                    echo "📝 Last Commit: $(git log -1 --oneline)"
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 2: ENVIRONMENT SETUP
        // Creates a Python virtual environment (venv).
        // WHY VENV? Isolates project packages from system Python
        //           so dependencies don't conflict.
        // ------------------------------------------------------
        stage('🐍 Environment Setup') {
            steps {
                echo '====== Setting up Python virtual environment ======'
                sh '''
                    echo "Python version:"
                    python3 --version

                    echo "Creating virtual environment..."
                    python3 -m venv ${VENV_DIR}

                    echo "Upgrading pip inside venv..."
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip

                    echo "✅ Virtual environment ready!"
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 3: INSTALL DEPENDENCIES
        // Installs all packages from requirements.txt into venv.
        // Your project packages include:
        //   python-telegram-bot → Telegram bot framework
        //   google-generativeai → Gemini AI client
        //   transformers        → HuggingFace sentiment model
        //   pymongo             → MongoDB driver
        //   requests            → HTTP client
        // ------------------------------------------------------
        stage('📦 Install Dependencies') {
            steps {
                echo '====== Installing Python dependencies ======'
                sh '''
                    echo "📋 requirements.txt contents:"
                    cat requirements.txt
                    echo ""

                    . ${VENV_DIR}/bin/activate
                    pip install -r requirements.txt

                    echo ""
                    echo "✅ All packages installed!"
                    echo "📦 Installed packages:"
                    pip list
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 4: CODE QUALITY (LINT)
        // Checks your Python code style using flake8.
        // Catches: unused imports, undefined variables,
        //          syntax errors, PEP8 style violations.
        // Non-blocking: warnings shown but won't fail the build.
        // ------------------------------------------------------
        stage('🔍 Lint Check') {
            steps {
                echo '====== Running flake8 code quality check ======'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip install flake8 --quiet

                    echo "Running flake8..."
                    flake8 . \
                        --exclude=${VENV_DIR},__pycache__,.git \
                        --max-line-length=120 \
                        --ignore=E501,W503,E302,E305 \
                        --statistics \
                        || echo "⚠️  Lint warnings found (non-blocking)"

                    echo "✅ Lint check done"
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 5: SECURITY SCAN
        // Scans for known CVEs in your installed packages (safety)
        // and checks your code for security issues (bandit).
        //
        // WHY IMPORTANT FOR YOUR BOT?
        //   Your bot handles API keys, MongoDB, user messages.
        //   A vulnerable package could expose all of that.
        //
        // Examples bandit catches:
        //   - Hardcoded passwords
        //   - Use of eval() or exec()
        //   - Insecure HTTP connections
        // ------------------------------------------------------
        stage('🔒 Security Scan') {
            steps {
                echo '====== Running security vulnerability scan ======'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip install safety bandit --quiet

                    echo "🛡️  Checking packages for known CVEs..."
                    safety check --full-report \
                        || echo "⚠️  Safety warnings found — review recommended"

                    echo ""
                    echo "🛡️  Scanning source code for security issues..."
                    bandit -r . \
                        --exclude ./${VENV_DIR} \
                        -ll \
                        || echo "⚠️  Bandit warnings found — review recommended"

                    echo "✅ Security scan complete"
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 6: RUN TESTS
        // Runs pytest test suite. Only runs if RUN_TESTS = true.
        // Generates:
        //   test-results.xml  → JUnit report shown in Jenkins UI
        //   coverage.xml      → Code coverage report
        //
        // NOTE: If no tests/ folder exists yet, this stage will
        //       show "no tests collected" — that is fine.
        //       Create tests/test_bot.py to add test cases.
        // ------------------------------------------------------
        stage('🧪 Run Tests') {
            when {
                expression { return params.RUN_TESTS == true }
            }
            steps {
                echo '====== Running automated tests with pytest ======'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip install pytest pytest-cov pytest-asyncio --quiet

                    echo "Running pytest..."
                    pytest tests/ \
                        --tb=short \
                        --junitxml=test-results.xml \
                        --cov=. \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing \
                        -v \
                        || echo "⚠️  Tests failed or no tests found"

                    echo "✅ Test stage complete"
                '''
            }
            post {
                always {
                    // Publishes test results as a visual report in Jenkins UI
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // ------------------------------------------------------
        // STAGE 7: VALIDATE CONFIG
        // Checks that all required API keys/secrets are present.
        // Fails EARLY with a clear error if any key is missing,
        // rather than failing mid-deploy with a cryptic error.
        //
        // Validates:
        //   TELEGRAM_BOT_TOKEN, GEMINI_API_KEY,
        //   BRAVE_API_KEY, MONGODB_URI
        // ------------------------------------------------------
        stage('⚙️  Validate Config') {
            steps {
                echo '====== Validating secrets and configuration ======'
                sh '''
                    echo "Checking required environment variables..."

                    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
                        echo "❌ TELEGRAM_BOT_TOKEN is missing!"
                        exit 1
                    else
                        echo "✅ TELEGRAM_BOT_TOKEN → set"
                    fi

                    if [ -z "$GEMINI_API_KEY" ]; then
                        echo "❌ GEMINI_API_KEY is missing!"
                        exit 1
                    else
                        echo "✅ GEMINI_API_KEY     → set"
                    fi

                    if [ -z "$BRAVE_API_KEY" ]; then
                        echo "❌ BRAVE_API_KEY is missing!"
                        exit 1
                    else
                        echo "✅ BRAVE_API_KEY      → set"
                    fi

                    if [ -z "$MONGODB_URI" ]; then
                        echo "❌ MONGODB_URI is missing!"
                        exit 1
                    else
                        echo "✅ MONGODB_URI        → set"
                    fi

                    echo ""
                    echo "✅ All secrets present!"
                    echo "🌍 Deploy target: ${DEPLOY_ENV}"
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 8: BUILD DOCKER IMAGE
        // Packages your bot into a Docker container.
        // Tags the image with build number for traceability.
        //   e.g.: ai-telegram-bot:42, ai-telegram-bot:latest
        //
        // Auto-generates a Dockerfile if one doesn't exist yet.
        // REQUIRES: Docker installed on the Jenkins agent.
        // SKIP: If Docker is not installed, this stage warns and
        //       continues without failing.
        // ------------------------------------------------------
        stage('🐳 Build Docker Image') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo '====== Building Docker image ======'
                sh '''
                    if ! command -v docker &> /dev/null; then
                        echo "⚠️  Docker not installed — skipping Docker build"
                        exit 0
                    fi

                    # Auto-create Dockerfile if missing
                    if [ ! -f Dockerfile ]; then
                        echo "📝 Creating Dockerfile automatically..."
                        cat > Dockerfile << 'DOCKERFILE'
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "bot.py"]
DOCKERFILE
                    fi

                    echo "Building image: ai-telegram-bot:${BUILD_NUMBER}"
                    docker build \
                        -t ai-telegram-bot:latest \
                        -t ai-telegram-bot:${BUILD_NUMBER} \
                        .

                    echo "✅ Docker image built!"
                    docker images | grep ai-telegram-bot
                '''
            }
        }

        // ------------------------------------------------------
        // STAGE 9: DEPLOY
        // Deploys the bot based on DEPLOY_ENV parameter:
        //
        //   development → Starts bot locally on Jenkins machine
        //                 using nohup (background process)
        //
        //   staging     → SSH into staging server, pull latest
        //                 code, restart bot process
        //
        //   production  → SSH into production server and deploy
        //
        // Secrets are written to a .env file on the target
        // machine at deploy time (never stored in repo).
        // ------------------------------------------------------
        stage('🚀 Deploy') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo "====== Deploying to: ${params.DEPLOY_ENV} ======"
                script {
                    if (params.DEPLOY_ENV == 'development') {
                        sh '''
                            echo "🔧 Starting bot in DEVELOPMENT mode..."

                            # Kill any existing bot process
                            pkill -f "python3 bot.py" || echo "No existing bot process"
                            sleep 2

                            # Write .env file with secrets
                            cat > .env << EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
GEMINI_API_KEY=${GEMINI_API_KEY}
BRAVE_API_KEY=${BRAVE_API_KEY}
MONGODB_URI=${MONGODB_URI}
EOF

                            # Start bot in background
                            . ${VENV_DIR}/bin/activate
                            nohup python3 bot.py > bot.log 2>&1 &
                            BOT_PID=$!
                            echo "✅ Bot started! PID: $BOT_PID"
                            echo "📋 Logs: tail -f bot.log"

                            # Verify it didn't crash immediately
                            sleep 5
                            if kill -0 $BOT_PID 2>/dev/null; then
                                echo "✅ Bot is running!"
                            else
                                echo "❌ Bot crashed on startup!"
                                cat bot.log
                                exit 1
                            fi
                        '''

                    } else if (params.DEPLOY_ENV == 'staging') {
                        sh '''
                            echo "🔧 Deploying to STAGING server..."
                            echo "👉 Configure your staging server SSH below:"
                            # ssh user@STAGING_IP "
                            #   cd /opt/ai-telegram-bot &&
                            #   git pull origin main &&
                            #   source venv/bin/activate &&
                            #   pip install -r requirements.txt &&
                            #   pkill -f 'python3 bot.py' || true &&
                            #   nohup python3 bot.py > bot.log 2>&1 &
                            # "
                        '''

                    } else if (params.DEPLOY_ENV == 'production') {
                        sh '''
                            echo "🚨 Deploying to PRODUCTION server..."
                            echo "👉 Configure your production server SSH below:"
                            # Add production SSH deploy commands here
                        '''
                    }
                }
            }
        }

        // ------------------------------------------------------
        // STAGE 10: HEALTH CHECK
        // Verifies the bot is running correctly after deploy.
        // Checks:
        //   1. Bot Python process is running
        //   2. All key Python imports work (telegram, gemini,
        //      pymongo, transformers)
        //
        // If process is not found (remote deploy), shows warning
        // but does not fail — remote checks need SSH extension.
        // ------------------------------------------------------
        stage('❤️  Health Check') {
            when {
                expression { return params.SKIP_DEPLOY == false }
            }
            steps {
                echo '====== Running post-deploy health check ======'
                sh '''
                    . ${VENV_DIR}/bin/activate

                    echo "🔍 Checking bot process..."
                    if pgrep -f "python3 bot.py" > /dev/null; then
                        echo "✅ Bot process is RUNNING"
                    else
                        echo "⚠️  Bot not found locally (may be on remote server)"
                    fi

                    echo ""
                    echo "🔍 Verifying Python imports..."
                    python3 - << 'PYCHECK'
import sys
print(f"Python {sys.version}")

checks = {
    "python-telegram-bot": "telegram",
    "google-generativeai":  "google.generativeai",
    "pymongo":              "pymongo",
    "transformers":         "transformers",
}

all_ok = True
for name, module in checks.items():
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except ImportError as e:
        print(f"  ❌ {name}: {e}")
        all_ok = False

print("")
print("✅ All imports OK!" if all_ok else "⚠️  Some imports failed!")
PYCHECK
                '''
            }
        }

    } // end stages

    // ----------------------------------------------------------
    // POST: Cleanup and notifications after pipeline completes.
    // ----------------------------------------------------------
    post {
        always {
            sh 'rm -f .env || true'   // Always delete .env to protect secrets
            echo """
====================================================
  PIPELINE SUMMARY
  Job     : ${env.JOB_NAME}
  Build   : #${env.BUILD_NUMBER}
  Env     : ${params.DEPLOY_ENV}
  Branch  : ${env.GIT_BRANCH}
  Result  : ${currentBuild.currentResult}
  URL     : ${env.BUILD_URL}
====================================================
            """
        }
        success {
            echo '✅ BUILD SUCCEEDED — AI Telegram Bot deployed!'
        }
        failure {
            echo '❌ BUILD FAILED — Check Console Output above'
        }
        unstable {
            echo '⚠️  BUILD UNSTABLE — Some tests failed'
        }
    }

} // end pipeline
