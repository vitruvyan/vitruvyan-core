"""
Vitruvyan Package Manager — install, remove, and manage .vit packages.

Package types:
  - service:   Docker-based microservice (e.g. neural-engine, mcp)
  - order:     Sacred Order governance module (core kernel component)
  - vertical:  Domain application meta-package (e.g. finance, healthcare)
  - extension: Optional plugin or adapter (e.g. mcp-tools, exporters)

Remote packages:
  - community: downloadable from GitHub Releases (no auth)
  - premium:   require license token via .vitruvyan/license.key or VIT_LICENSE_TOKEN
"""
