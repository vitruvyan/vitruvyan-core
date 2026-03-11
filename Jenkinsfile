/*
 * Vitruvyan OS — CI/CD Pipeline
 * ──────────────────────────────
 * Quality gate + multi-service Docker build + release automation.
 *
 * Pipeline stages:
 *   1. Install        → Python venv + dependencies
 *   2. Quality Gate   → Unit tests, architectural tests, contract validation, smoke tests
 *   3. Docker Build   → Parallel build of all service images
 *   4. Docker Push    → Push images to registry (manual trigger)
 *   5. Release        → Tag + GitHub Release (manual trigger, main branch only)
 *
 * Triggers:
 *   - Every push to any branch → Stages 1-3 (quality gate)
 *   - Manual "Push Images"     → Stage 4
 *   - Manual "Create Release"  → Stage 5 (main only)
 */

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  parameters {
    string(name: 'DOCKER_REGISTRY', defaultValue: 'vitruvyan', description: 'Docker registry prefix (e.g. vitruvyan, ghcr.io/dbaldoni)')
    string(name: 'DOCKER_REGISTRY_CREDENTIALS_ID', defaultValue: 'docker-registry', description: 'Jenkins credentials ID for Docker registry')
    booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push Docker images to registry after build')
    booleanParam(name: 'CREATE_RELEASE', defaultValue: false, description: 'Create a GitHub Release (main branch only)')
    string(name: 'RELEASE_VERSION', defaultValue: '', description: 'Release version (e.g. 1.16.0). Leave empty for auto-increment.')
  }

  environment {
    PYTHONPATH = "${WORKSPACE}/vitruvyan_core:${WORKSPACE}"
    IMAGE_TAG  = "${env.BUILD_NUMBER}"
  }

  stages {

    // ── Stage 1: Install ──────────────────────────────────────────
    stage('Install') {
      steps {
        sh '''
          set -eu
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip setuptools wheel -q
          pip install -e ".[dev]" -q
        '''
      }
    }

    // ── Stage 2: Quality Gate ─────────────────────────────────────
    stage('Quality Gate') {
      parallel {

        stage('Unit + Integration Tests') {
          steps {
            sh '''
              set -eu
              . .venv/bin/activate
              pytest -m "not e2e" \
                --tb=short \
                --no-header \
                -q \
                --junit-xml=reports/test-results.xml \
                || true
            '''
          }
          post {
            always {
              junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
            }
          }
        }

        stage('Architectural Tests') {
          steps {
            sh '''
              set -eu
              . .venv/bin/activate
              pytest -m "architectural" \
                --tb=short \
                -q \
                --junit-xml=reports/arch-results.xml \
                || true
            '''
          }
          post {
            always {
              junit allowEmptyResults: true, testResults: 'reports/arch-results.xml'
            }
          }
        }

        stage('Contract Validation') {
          steps {
            sh '''
              set -eu
              . .venv/bin/activate
              python3 -c "
from vitruvyan_core.core.platform.update_manager.ci.contract_validator import (
    ContractValidator, discover_verticals
)
validator = ContractValidator(core_contracts_major=1)
manifests = discover_verticals('.')
results = validator.validate_multiple(manifests)
errors = [r for r in results if not r.valid]
for r in results:
    status = 'PASS' if r.valid else 'FAIL'
    print(f'  [{status}] {r.manifest_path}')
    for e in r.errors:
        print(f'         ERROR: {e}')
    for w in r.warnings:
        print(f'         WARN:  {w}')
if errors:
    raise SystemExit(f'{len(errors)} manifest(s) failed validation')
print(f'All {len(results)} manifest(s) valid')
"
            '''
          }
        }

        stage('Smoke Tests') {
          steps {
            sh '''
              set -eu
              export PYTHONPATH="${WORKSPACE}/vitruvyan_core:${WORKSPACE}:${PYTHONPATH:-}"
              bash smoke_tests/run.sh
            '''
          }
        }
      }
    }

    // ── Stage 3: Docker Build (parallel per-service) ──────────────
    stage('Docker Build') {
      parallel {

        stage('graph') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_graph \
                -t ${params.DOCKER_REGISTRY}/vit-graph:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-graph:latest \
                .
            """
          }
        }

        stage('babel-gardens') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_babel_gardens \
                -t ${params.DOCKER_REGISTRY}/vit-babel-gardens:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-babel-gardens:latest \
                .
            """
          }
        }

        stage('memory-orders') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_memory_orders \
                -t ${params.DOCKER_REGISTRY}/vit-memory-orders:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-memory-orders:latest \
                .
            """
          }
        }

        stage('vault-keepers') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.vault_keepers \
                -t ${params.DOCKER_REGISTRY}/vit-vault-keepers:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-vault-keepers:latest \
                .
            """
          }
        }

        stage('orthodoxy-wardens') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens \
                -t ${params.DOCKER_REGISTRY}/vit-orthodoxy-wardens:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-orthodoxy-wardens:latest \
                .
            """
          }
        }

        stage('codex-hunters') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_codex_hunters \
                -t ${params.DOCKER_REGISTRY}/vit-codex-hunters:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-codex-hunters:latest \
                .
            """
          }
        }

        stage('pattern-weavers') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_pattern_weavers \
                -t ${params.DOCKER_REGISTRY}/vit-pattern-weavers:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-pattern-weavers:latest \
                .
            """
          }
        }

        stage('embedding') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_embedding \
                -t ${params.DOCKER_REGISTRY}/vit-embedding:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-embedding:latest \
                .
            """
          }
        }

        stage('conclave') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_conclave \
                -t ${params.DOCKER_REGISTRY}/vit-conclave:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-conclave:latest \
                .
            """
          }
        }

        stage('neural-engine') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_neural_engine \
                -t ${params.DOCKER_REGISTRY}/vit-neural-engine:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-neural-engine:latest \
                .
            """
          }
        }

        stage('mcp') {
          steps {
            sh """
              docker build \
                -f infrastructure/docker/dockerfiles/Dockerfile.api_mcp \
                -t ${params.DOCKER_REGISTRY}/vit-mcp:${IMAGE_TAG} \
                -t ${params.DOCKER_REGISTRY}/vit-mcp:latest \
                .
            """
          }
        }
      }
    }

    // ── Stage 4: Docker Push (manual) ─────────────────────────────
    stage('Docker Push') {
      when {
        expression { return params.PUSH_IMAGES }
      }
      steps {
        withCredentials([usernamePassword(
          credentialsId: "${params.DOCKER_REGISTRY_CREDENTIALS_ID}",
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_PASS'
        )]) {
          sh '''
            set -eu
            printf '%s' "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin

            SERVICES="graph babel-gardens memory-orders vault-keepers orthodoxy-wardens codex-hunters pattern-weavers embedding conclave neural-engine mcp"

            for svc in $SERVICES; do
              echo "Pushing vit-${svc}..."
              docker push "${DOCKER_REGISTRY}/vit-${svc}:${IMAGE_TAG}"
              docker push "${DOCKER_REGISTRY}/vit-${svc}:latest"
            done

            docker logout
          '''
        }
      }
    }

    // ── Stage 5: Create Release (manual, main only) ───────────────
    stage('Release') {
      when {
        allOf {
          expression { return params.CREATE_RELEASE }
          branch 'main'
        }
      }
      steps {
        sh '''
          set -eu
          . .venv/bin/activate

          # Determine version
          if [ -n "${RELEASE_VERSION}" ]; then
            VERSION="${RELEASE_VERSION}"
          else
            # Auto-increment: read latest tag, bump patch
            LATEST=$(git tag -l "v*" --sort=-v:refname | head -1 | sed 's/^v//')
            if [ -z "$LATEST" ]; then
              VERSION="1.0.0"
            else
              MAJOR=$(echo "$LATEST" | cut -d. -f1)
              MINOR=$(echo "$LATEST" | cut -d. -f2)
              PATCH=$(echo "$LATEST" | cut -d. -f3)
              VERSION="${MAJOR}.${MINOR}.$((PATCH + 1))"
            fi
          fi

          echo "Creating release v${VERSION}..."

          # Tag
          git tag -a "v${VERSION}" -m "Release v${VERSION} — build #${BUILD_NUMBER}"
          git push origin "v${VERSION}"

          echo "Tagged v${VERSION}. GitHub Release can be created from this tag."
          echo "RELEASE_VERSION=${VERSION}" > release.properties
        '''
        archiveArtifacts artifacts: 'release.properties', allowEmptyArchive: true
      }
    }
  }

  post {
    success {
      echo "Pipeline completed successfully. Build #${env.BUILD_NUMBER}"
    }
    failure {
      echo "Pipeline FAILED at build #${env.BUILD_NUMBER}. Check logs above."
    }
    always {
      sh 'mkdir -p reports'
    }
  }
}
