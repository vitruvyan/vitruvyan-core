# .vit File Format Specification v1.0
#
# A .vit file is a YAML manifest that describes a Vitruvyan package.
# Like .deb (Debian) or .apk (Android), the .vit extension identifies
# installable components of the Vitruvyan OS ecosystem.
#
# Internal format: YAML 1.2
# Extension: .vit
# Location: vitruvyan_core/core/platform/package_manager/packages/manifests/
#
# ─── Required Fields ───────────────────────────────────────────────
#
#   package_name     Unique identifier (pattern: <type>-<name>)
#   package_version  SemVer (e.g. 1.2.0, 2.0.0-beta.1)
#   package_type     One of: service | order | vertical | extension
#   status           One of: stable | beta | experimental | deprecated
#   description      Human-readable purpose (1 line)
#   tier             One of: core | package
#                    core = updated via 'vit upgrade' (Sacred Orders, Graph, Bus)
#                    package = installed via 'vit install' (optional components)
#
# ─── Optional Fields ───────────────────────────────────────────────
#
#   homepage         URL to documentation
#   sacred_order     Epistemic category (perception | memory | reason | discourse | truth)
#
# ─── Compatibility Section ─────────────────────────────────────────
#
#   compatibility:
#     min_core_version   Minimum Vitruvyan Core version required
#     max_core_version   Maximum (use wildcards: 1.x.x)
#     contracts_major    Contract interface major version
#     conflicts_with     List of incompatible packages
#
# ─── Dependencies Section ──────────────────────────────────────────
#
#   dependencies:
#     required           List of required packages (with version constraints)
#     optional           List of optional enhancing packages
#     system             System requirements (docker, redis, postgres, qdrant)
#
# ─── Installation Section ──────────────────────────────────────────
#
#   installation:
#     method             One of: docker_compose | pip | script
#     compose_service    Service name in docker-compose.yml
#     compose_file       Path to compose file (default: infrastructure/docker/docker-compose.yml)
#     dockerfile         Path to Dockerfile
#     ports              List of port mappings ("host:container")
#     env_required       Environment variables that MUST be set
#     env_optional       Environment variables with defaults
#     init_commands      Post-install initialization commands
#
# ─── Health & Testing ──────────────────────────────────────────────
#
#   health:
#     endpoint           Health check URL (e.g. http://localhost:9003/health)
#     interval           Check interval in seconds (default: 30)
#     timeout            Timeout in seconds (default: 10)
#
#   smoke_tests:
#     path               Path to smoke test script or directory
#     timeout            Max seconds for smoke tests (default: 120)
#
# ─── Uninstallation Section ────────────────────────────────────────
#
#   uninstallation:
#     preserve_data      Keep data files after removal (default: true)
#     cleanup_streams    Remove Redis Streams channels (default: false)
#     cleanup_commands   Shell commands to run during removal
#
# ─── Ownership ─────────────────────────────────────────────────────
#
#   ownership:
#     team               Responsible team name
#     contact            Email or URL
#
# ─── Example ───────────────────────────────────────────────────────
#
#   See: service-neural-engine.vit (simple service package)
#   See: order-babel-gardens.vit (core kernel component)
#   See: vertical-finance.vit (meta-package with dependencies)
#
