pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    DOCKER_IMAGE_REPO = "${params.DOCKER_IMAGE_REPO ?: 'vitruvyan/vitruvyan-core'}"
    DOCKER_CONTEXT = "${params.DOCKER_CONTEXT ?: '.'}"
    DOCKERFILE_PATH = "${params.DOCKERFILE_PATH ?: 'infrastructure/docker/dockerfiles/Dockerfile.api_graph'}"
    DOCKER_REGISTRY_CREDENTIALS_ID = "${params.DOCKER_REGISTRY_CREDENTIALS_ID ?: 'docker-registry'}"
    IMAGE_TAG = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('checkout') {
      steps {
        checkout scm
      }
    }

    stage('install') {
      steps {
        sh '''
          set -eux
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip setuptools wheel
          pip install -e .[dev]
        '''
      }
    }

    stage('test') {
      steps {
        sh '''
          set -eux
          . .venv/bin/activate
          pytest -m "not e2e"
        '''
      }
    }

    stage('docker-build') {
      steps {
        sh '''
          set -eux
          docker build -f "${DOCKERFILE_PATH}" -t "${DOCKER_IMAGE_REPO}:${IMAGE_TAG}" "${DOCKER_CONTEXT}"
          docker tag "${DOCKER_IMAGE_REPO}:${IMAGE_TAG}" "${DOCKER_IMAGE_REPO}:latest"
        '''
      }
    }

    stage('docker-push') {
      when {
        expression { return params.PUSH_IMAGE }
      }
      steps {
        withCredentials([usernamePassword(
          credentialsId: "${DOCKER_REGISTRY_CREDENTIALS_ID}",
          usernameVariable: 'DOCKER_USERNAME',
          passwordVariable: 'DOCKER_PASSWORD'
        )]) {
          sh '''
            set -eux
            printf '%s' "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin
            docker push "${DOCKER_IMAGE_REPO}:${IMAGE_TAG}"
            docker push "${DOCKER_IMAGE_REPO}:latest"
          '''
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
  }
}
