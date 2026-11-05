pipeline {
  agent { docker { image 'node:24' } }

  triggers {
    cron('0 0 * * *')
  }

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  environment {
    GITHUB_USER = 'ngthanhvu'
    REPO_URL    = 'github.com/ngthanhvu/ngthanhvu.git'
  }

  stages {
    stage('Generate Snake') {
      steps {
        withCredentials([string(credentialsId: 'github-pat', variable: 'GHPAT')]) {
          sh '''
            mkdir -p dist
            npx --yes generate-snake-animation@3 \
              --github_user=$GITHUB_USER \
              --github_token=$GHPAT \
              --output=dist/github-snake.svg \
              "--output=dist/github-snake-dark.svg?palette=github-dark"
          '''
        }
      }
    }

    stage('Push to output branch') {
      steps {
        withCredentials([string(credentialsId: 'github-pat', variable: 'GHPAT')]) {
          sh '''
            rm -rf out
            git clone --branch output --single-branch \
              https://x-access-token:$GHPAT@$REPO_URL out \
            || {
              git clone https://x-access-token:$GHPAT@$REPO_URL out
              git -C out checkout --orphan output
              git -C out rm -rf --quiet . || true
            }
            cp dist/github-snake.svg dist/github-snake-dark.svg out/
            git -C out add github-snake.svg github-snake-dark.svg
            git -C out -c user.name=jenkins -c user.email=jenkins@ci \
              commit -m "chore: update snake animation [skip ci]" || true
            git -C out push origin output
          '''
        }
      }
    }
  }

  post {
    failure {
      echo 'Snake generation failed - check github-pat credential and network access to api.github.com'
    }
  }
}
