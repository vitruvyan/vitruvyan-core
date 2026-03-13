/*
 * Vitruvyan OS — CI/CD Pipeline
 * ──────────────────────────────
 * Smart change detection + quality gate + per-package Docker build + release.
 *
 * Pipeline stages:
 *   1. Install            → Python venv + dependencies
 *   2. Change Detection   → Detect which packages/services changed since last green build
 *   3. Quality Gate       → Unit tests, architectural tests, contract validation, smoke tests
 *   4. Docker Build       → Build only changed service images (or all if core changed)
 *   5. Deploy Local       → Restart changed services on this VPS (auto, skip with DEPLOY_LOCAL=false)
 *   6. Docker Push        → Push changed images to registry (manual trigger)
 *   7. Release            → Per-package version tags + monorepo tag (manual, main only)
 *
 * Change detection:
 *   - Core change (vitruvyan_core/core/, contracts, tests) → rebuild ALL services
 *   - Service-only change (services/api_*) → rebuild only affected service(s)
 *   - Docs/scripts-only change → skip Docker build entirely
 *
 * Triggers:
 *   - Every push to any branch → Stages 1-5
 *   - Manual "Push Images"     → Stage 6
 *   - Manual "Create Release"  → Stage 7 (main only)
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
    booleanParam(name: 'DEPLOY_LOCAL', defaultValue: true, description: 'Restart changed services on this VPS after build (set false to skip deploy)')
    booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push Docker images to registry after build')
    booleanParam(name: 'BUILD_ALL', defaultValue: false, description: 'Force build all services (skip change detection)')
    booleanParam(name: 'CREATE_RELEASE', defaultValue: false, description: 'Create a GitHub Release (main branch only)')
    string(name: 'RELEASE_VERSION', defaultValue: '', description: 'Release version (e.g. 1.16.0). Leave empty for auto-increment.')
  }

  triggers {
    // Fallback: poll every 5 minutes in case the GitHub webhook is not configured.
    // When https://build.vitruvyan.com/github-webhook/ is registered as a push
    // webhook on vitruvyan/vitruvyan-core the GitHubPushTrigger in the job config
    // fires immediately and the poll never runs (Jenkins deduplicates).
    pollSCM('H/5 * * * *')
  }

  environment {
    PYTHONPATH      = "${WORKSPACE}/vitruvyan_core:${WORKSPACE}"
    IMAGE_TAG       = "${env.BUILD_NUMBER}"
    // Override any stale DOCKER_CONTEXT job parameter — Docker CLI uses this
    // env var to select a named context; "." would cause build failures.
    DOCKER_CONTEXT  = 'default'
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

    // ── Stage 2: Change Detection ─────────────────────────────────
    stage('Change Detection') {
      steps {
        script {
          // Service directory → image name mapping
          def serviceMap = [
            'services/api_graph'             : 'graph',
            'services/api_babel_gardens'     : 'babel-gardens',
            'services/api_memory_orders'     : 'memory-orders',
            'services/api_vault_keepers'     : 'vault-keepers',
            'services/api_orthodoxy_wardens' : 'orthodoxy-wardens',
            'services/api_codex_hunters'     : 'codex-hunters',
            'services/api_pattern_weavers'   : 'pattern-weavers',
            'services/api_embedding'         : 'embedding',
            'services/api_conclave'          : 'conclave',
            'services/api_neural_engine'     : 'neural-engine',
            'services/api_mcp'              : 'mcp',
          ]

          // Core paths — if ANY of these change, rebuild ALL services
          def corePaths = [
            'vitruvyan_core/core/',
            'vitruvyan_core/contracts/',
            'infrastructure/docker/',
            'pyproject.toml',
            'Jenkinsfile',
          ]

          // Skip paths — changes here don't trigger Docker builds
          def skipPaths = ['docs/', 'scripts/', '.github/', 'ui/', 'README', 'mkdocs', '.md']

          if (params.BUILD_ALL) {
            echo "BUILD_ALL=true — building all services"
            env.CHANGED_SERVICES = serviceMap.values().join(',')
            env.CORE_CHANGED = 'true'
          } else {
            // Get changed files since last successful build (or HEAD~1 for first build)
            def lastGreen = currentBuild.previousSuccessfulBuild?.getId()
            def changedFiles = []
            if (lastGreen) {
              changedFiles = sh(
                script: "git diff --name-only HEAD...\$(git log -1 --format='%H' ${lastGreen}) 2>/dev/null || git diff --name-only HEAD~1",
                returnStdout: true
              ).trim().split('\n').findAll { it }
            } else {
              changedFiles = sh(
                script: "git diff --name-only HEAD~1 2>/dev/null || git ls-files",
                returnStdout: true
              ).trim().split('\n').findAll { it }
            }

            echo "Changed files (${changedFiles.size()}):\n${changedFiles.take(30).join('\n')}"
            if (changedFiles.size() > 30) echo "... and ${changedFiles.size() - 30} more"

            // Check if core changed
            def coreChanged = changedFiles.any { f -> corePaths.any { p -> f.startsWith(p) } }
            env.CORE_CHANGED = coreChanged.toString()

            if (coreChanged) {
              echo "Core paths changed — all services will be rebuilt"
              env.CHANGED_SERVICES = serviceMap.values().join(',')
            } else {
              // Find which services changed
              def changed = [] as Set
              changedFiles.each { f ->
                serviceMap.each { dir, name ->
                  if (f.startsWith(dir)) changed.add(name)
                }
              }

              if (changed.isEmpty()) {
                // Check if ONLY skip-paths changed
                def onlySkip = changedFiles.every { f -> skipPaths.any { p -> f.startsWith(p) || f.contains(p) } }
                if (onlySkip) {
                  echo "Only docs/scripts changed — no Docker builds needed"
                } else {
                  echo "Non-service changes detected — building all as safety net"
                  changed.addAll(serviceMap.values())
                }
              }

              env.CHANGED_SERVICES = changed.join(',')
              echo "Services to build: ${env.CHANGED_SERVICES ?: '(none)'}"
            }
          }
        }
      }
    }

    // ── Stage 3: Quality Gate ─────────────────────────────────────
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
              . .venv/bin/activate
              export PYTHONPATH="${WORKSPACE}/vitruvyan_core:${WORKSPACE}:${PYTHONPATH:-}"
              bash smoke_tests/run.sh
            '''
          }
        }
      }
    }

    // ── Stage 4: Docker Build (smart — only changed services) ────
    stage('Docker Build') {
      when {
        expression { return env.CHANGED_SERVICES?.trim() }
      }
      steps {
        script {
          // Dockerfile mapping (image name → Dockerfile path)
          def dockerfileMap = [
            'graph'             : 'infrastructure/docker/dockerfiles/Dockerfile.api_graph',
            'babel-gardens'     : 'infrastructure/docker/dockerfiles/Dockerfile.api_babel_gardens',
            'memory-orders'     : 'infrastructure/docker/dockerfiles/Dockerfile.api_memory_orders',
            'vault-keepers'     : 'infrastructure/docker/dockerfiles/Dockerfile.vault_keepers',
            'orthodoxy-wardens' : 'infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens',
            'codex-hunters'     : 'infrastructure/docker/dockerfiles/Dockerfile.api_codex_hunters',
            'pattern-weavers'   : 'infrastructure/docker/dockerfiles/Dockerfile.api_weavers',
            'embedding'         : 'infrastructure/docker/dockerfiles/Dockerfile.api_embedding',
            'conclave'          : 'infrastructure/docker/dockerfiles/Dockerfile.api_conclave',
            'neural-engine'     : 'infrastructure/docker/dockerfiles/Dockerfile.api_neural',
            'mcp'               : 'infrastructure/docker/dockerfiles/Dockerfile.api_mcp',
          ]

          def services = env.CHANGED_SERVICES.split(',').findAll { it.trim() }
          def total = services.size()
          echo "Building ${total} service(s): ${services.join(', ')}"

          // Build in parallel batches
          def parallelStages = [:]
          services.each { svc ->
            def dockerfile = dockerfileMap[svc]
            if (!dockerfile) {
              echo "WARNING: No Dockerfile mapping for '${svc}' — skipping"
              return
            }
            parallelStages[svc] = {
              sh """
                docker build \
                  -f ${dockerfile} \
                  -t ${params.DOCKER_REGISTRY}/vit-${svc}:${IMAGE_TAG} \
                  -t ${params.DOCKER_REGISTRY}/vit-${svc}:latest \
                  .
              """
            }
          }
          parallel parallelStages
          echo "Built ${total} image(s) successfully"
        }
      }
    }

    // ── Stage 5: Deploy Local (auto, only changed services) ──────
    stage('Deploy Local') {
      when {
        allOf {
          expression { return params.DEPLOY_LOCAL }
          expression { return env.CHANGED_SERVICES?.trim() }
        }
      }
      steps {
        script {
          // Map pipeline service names → compose service names (+ listeners)
          def composeMap = [
            'graph'             : ['graph'],
            'babel-gardens'     : ['babel_gardens', 'babel_listener'],
            'memory-orders'     : ['memory_orders', 'memory_orders_listener'],
            'vault-keepers'     : ['vault_keepers', 'vault_listener'],
            'orthodoxy-wardens' : ['orthodoxy_wardens', 'orthodoxy_listener'],
            'codex-hunters'     : ['codex_hunters', 'codex_listener'],
            'pattern-weavers'   : ['pattern_weavers'],
            'embedding'         : ['embedding'],
            'conclave'          : ['conclave', 'conclave_listener'],
            'neural-engine'     : ['neural_engine'],
            'mcp'               : ['mcp'],
          ]

          def services = env.CHANGED_SERVICES.split(',').findAll { it.trim() }
          def composeSvcs = services.collectMany { svc -> composeMap[svc] ?: [] }

          if (composeSvcs.isEmpty()) {
            echo "No compose services to deploy — skipping"
            return
          }

          echo "Deploying ${composeSvcs.size()} container(s): ${composeSvcs.join(', ')}"
          sh """
            cd infrastructure/docker
            docker compose up -d --no-deps --no-build ${composeSvcs.join(' ')}
          """
          echo "Deploy complete"
        }
      }
    }

    // ── Stage 6: Docker Push (manual, only changed services) ─────
    stage('Docker Push') {
      when {
        allOf {
          expression { return params.PUSH_IMAGES }
          expression { return env.CHANGED_SERVICES?.trim() }
        }
      }
      steps {
        withCredentials([usernamePassword(
          credentialsId: "${params.DOCKER_REGISTRY_CREDENTIALS_ID}",
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_PASS'
        )]) {
          script {
            sh 'printf \'%s\' "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin'

            def services = env.CHANGED_SERVICES.split(',').findAll { it.trim() }
            services.each { svc ->
              echo "Pushing vit-${svc}..."
              sh "docker push '${params.DOCKER_REGISTRY}/vit-${svc}:${IMAGE_TAG}'"
              sh "docker push '${params.DOCKER_REGISTRY}/vit-${svc}:latest'"
            }

            sh 'docker logout'
          }
        }
      }
    }

    // ── Stage 7: Release (manual, main only) ─────────────────────
    //   Creates monorepo tag (v1.16.0) + per-package tags (vit-neural-engine/2.1.0)
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

          # Determine monorepo version
          if [ -n "${RELEASE_VERSION}" ]; then
            VERSION="${RELEASE_VERSION}"
          else
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

          echo "Creating monorepo release v${VERSION}..."
          git tag -a "v${VERSION}" -m "Release v${VERSION} — build #${BUILD_NUMBER}"

          echo "RELEASE_VERSION=${VERSION}" > release.properties
          echo "RELEASE_PACKAGES=" >> release.properties
        '''

        // Per-package version tags from .vit manifests
        script {
          def services = env.CHANGED_SERVICES?.split(',')?.findAll { it.trim() } ?: []
          if (services) {
            sh '''
              set -eu
              . .venv/bin/activate
              python3 -c "
import yaml, glob, os
manifests = glob.glob('vitruvyan_core/core/platform/package_manager/packages/manifests/*.vit')
tags = []
for m in manifests:
    with open(m) as f:
        data = yaml.safe_load(f)
    name = data.get('package_name', '')
    ver = data.get('package_version', '')
    if name and ver:
        tag = f'{name}/{ver}'
        tags.append(tag)
        print(f'  Package tag: {tag}')
# Write tags for git
with open('package_tags.txt', 'w') as f:
    f.write('\\n'.join(tags))
"
              # Create per-package tags (idempotent — skip if tag exists)
              while IFS= read -r tag; do
                if [ -n "$tag" ] && ! git rev-parse "$tag" >/dev/null 2>&1; then
                  git tag -a "$tag" -m "Package release: $tag — build #${BUILD_NUMBER}"
                  echo "  Tagged: $tag"
                else
                  echo "  Skip (exists): $tag"
                fi
              done < package_tags.txt
              rm -f package_tags.txt
            '''
          }
        }

        // Generate release_metadata.json from .vit manifests + git log
        sh '''
          set -eu
          . .venv/bin/activate

          # Read version from release.properties
          VERSION=$(grep RELEASE_VERSION release.properties | cut -d= -f2)

          python3 -c "
import yaml, glob, json
from datetime import datetime, timezone

version = '${VERSION}'
manifests = glob.glob('vitruvyan_core/core/platform/package_manager/packages/manifests/*.vit')
packages = []
for m in manifests:
    if 'TEMPLATE' in m:
        continue
    with open(m) as f:
        data = yaml.safe_load(f)
    packages.append({
        'name': data.get('package_name', ''),
        'version': data.get('package_version', ''),
        'type': data.get('package_type', ''),
        'tier': data.get('tier', ''),
        'status': data.get('status', 'stable'),
    })

metadata = {
    'version': version,
    'channel': 'stable',
    'release_date': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'packages': sorted(packages, key=lambda p: p['name']),
}

with open('release_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print(f'Generated release_metadata.json for v{version} with {len(packages)} packages')
"
        '''

        sh '''
          set -eu
          git push origin --tags
          echo "All tags pushed."
        '''

        // Create GitHub Release with metadata asset (requires gh CLI)
        sh '''
          set -eu
          VERSION=$(grep RELEASE_VERSION release.properties | cut -d= -f2)
          if command -v gh >/dev/null 2>&1; then
            CHANGELOG=$(git log --oneline --no-merges "$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo HEAD~10)..HEAD" | head -20)
            gh release create "v${VERSION}" \
              --title "v${VERSION}" \
              --notes "${CHANGELOG}" \
              release_metadata.json || echo "GitHub Release creation skipped (may already exist)"
          else
            echo "gh CLI not available — skipping GitHub Release creation"
          fi
        '''
        archiveArtifacts artifacts: 'release.properties,release_metadata.json', allowEmptyArchive: true
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
