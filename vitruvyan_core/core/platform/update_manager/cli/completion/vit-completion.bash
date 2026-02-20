#!/usr/bin/env bash
# Bash completion script for vit (Vitruvyan Package Manager)
# Installation: source this file or copy to /etc/bash_completion.d/vit

_vit_completion() {
    local cur prev words cword
    _init_completion || return

    # Commands
    local commands="update upgrade plan rollback status channel install remove list search info help"
    
    # Global flags
    local global_flags="--help --version --verbose --quiet"
    
    # Command-specific flags
    local update_flags="--channel --json"
    local upgrade_flags="--channel --target --yes --json"
    local plan_flags="--target --channel --json"
    local rollback_flags="--yes"
    local status_flags="--json"
    local channel_flags=""
    local install_flags="--channel --version --yes --json"
    local remove_flags="--purge --yes"
    local list_flags="--all --type --json"
    local search_flags="--type --json"
    local info_flags="--json"
    
    # Channel values
    local channels="stable beta"
    
    # Package types
    local package_types="service order vertical extension"
    
    # Get current command (first word after 'vit')
    local command=""
    local i
    for (( i=1; i < ${#words[@]} - 1; i++ )); do
        if [[ ${words[i]} != -* ]]; then
            command=${words[i]}
            break
        fi
    done
    
    # Complete based on position
    case "${prev}" in
        vit)
            # Completing command
            COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
            return 0
            ;;
        --channel)
            # Completing channel value
            COMPREPLY=( $(compgen -W "${channels}" -- "${cur}") )
            return 0
            ;;
        --type)
            # Completing package type
            COMPREPLY=( $(compgen -W "${package_types}" -- "${cur}") )
            return 0
            ;;
        --target|--version)
            # Completing version (could fetch from registry, for now just hint)
            COMPREPLY=( $(compgen -W "1.0.0 1.1.0 1.2.0" -- "${cur}") )
            return 0
            ;;
        update)
            COMPREPLY=( $(compgen -W "${update_flags}" -- "${cur}") )
            return 0
            ;;
        upgrade)
            COMPREPLY=( $(compgen -W "${upgrade_flags}" -- "${cur}") )
            return 0
            ;;
        plan)
            COMPREPLY=( $(compgen -W "${plan_flags}" -- "${cur}") )
            return 0
            ;;
        rollback)
            COMPREPLY=( $(compgen -W "${rollback_flags}" -- "${cur}") )
            return 0
            ;;
        status)
            COMPREPLY=( $(compgen -W "${status_flags}" -- "${cur}") )
            return 0
            ;;
        channel)
            # Channel command takes channel name as argument
            COMPREPLY=( $(compgen -W "${channels} ${channel_flags}" -- "${cur}") )
            return 0
            ;;
        install)
            # Complete with package names (fetch from manifest directory)
            local packages=""
            if [ -d "vitruvyan_core/core/platform/update_manager/packages/manifests" ]; then
                packages=$(find vitruvyan_core/core/platform/update_manager/packages/manifests -name "*.yaml" -exec basename {} .yaml \; 2>/dev/null | tr '\n' ' ')
            fi
            # Also add common aliases
            packages="${packages} babel_gardens neural_engine pattern_weavers orthodoxy_wardens vault_keepers memory_orders"
            COMPREPLY=( $(compgen -W "${packages} ${install_flags}" -- "${cur}") )
            return 0
            ;;
        remove)
            # Complete with installed package names (from .vitruvyan/installed_packages.json)
            local installed=""
            if [ -f ".vitruvyan/installed_packages.json" ]; then
                installed=$(python3 -c "import json; print(' '.join([p['name'] for p in json.load(open('.vitruvyan/installed_packages.json'))['packages']]))" 2>/dev/null)
            fi
            COMPREPLY=( $(compgen -W "${installed} ${remove_flags}" -- "${cur}") )
            return 0
            ;;
        list)
            COMPREPLY=( $(compgen -W "${list_flags}" -- "${cur}") )
            return 0
            ;;
        search)
            # No completion for search query, just flags
            COMPREPLY=( $(compgen -W "${search_flags}" -- "${cur}") )
            return 0
            ;;
        info)
            # Complete with all known package names
            local all_packages=""
            if [ -d "vitruvyan_core/core/platform/update_manager/packages/manifests" ]; then
                all_packages=$(find vitruvyan_core/core/platform/update_manager/packages/manifests -name "*.yaml" -exec basename {} .yaml \; 2>/dev/null | tr '\n' ' ')
            fi
            COMPREPLY=( $(compgen -W "${all_packages} ${info_flags}" -- "${cur}") )
            return 0
            ;;
    esac
    
    # Default: complete with commands if no command yet
    if [ -z "${command}" ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return 0
    fi
    
    # Complete with flags for current command
    case "${command}" in
        update)
            COMPREPLY=( $(compgen -W "${update_flags}" -- "${cur}") )
            ;;
        upgrade)
            COMPREPLY=( $(compgen -W "${upgrade_flags}" -- "${cur}") )
            ;;
        plan)
            COMPREPLY=( $(compgen -W "${plan_flags}" -- "${cur}") )
            ;;
        rollback)
            COMPREPLY=( $(compgen -W "${rollback_flags}" -- "${cur}") )
            ;;
        status)
            COMPREPLY=( $(compgen -W "${status_flags}" -- "${cur}") )
            ;;
        channel)
            COMPREPLY=( $(compgen -W "${channels}" -- "${cur}") )
            ;;
        install)
            local packages=""
            if [ -d "vitruvyan_core/core/platform/update_manager/packages/manifests" ]; then
                packages=$(find vitruvyan_core/core/platform/update_manager/packages/manifests -name "*.yaml" -exec basename {} .yaml \; 2>/dev/null | tr '\n' ' ')
            fi
            packages="${packages} babel_gardens neural_engine pattern_weavers"
            COMPREPLY=( $(compgen -W "${packages} ${install_flags}" -- "${cur}") )
            ;;
        remove)
            local installed=""
            if [ -f ".vitruvyan/installed_packages.json" ]; then
                installed=$(python3 -c "import json; print(' '.join([p['name'] for p in json.load(open('.vitruvyan/installed_packages.json'))['packages']]))" 2>/dev/null)
            fi
            COMPREPLY=( $(compgen -W "${installed} ${remove_flags}" -- "${cur}") )
            ;;
        list)
            COMPREPLY=( $(compgen -W "${list_flags}" -- "${cur}") )
            ;;
        search)
            COMPREPLY=( $(compgen -W "${search_flags}" -- "${cur}") )
            ;;
        info)
            local all_packages=""
            if [ -d "vitruvyan_core/core/platform/update_manager/packages/manifests" ]; then
                all_packages=$(find vitruvyan_core/core/platform/update_manager/packages/manifests -name "*.yaml" -exec basename {} .yaml \; 2>/dev/null | tr '\n' ' ')
            fi
            COMPREPLY=( $(compgen -W "${all_packages} ${info_flags}" -- "${cur}") )
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
    
    return 0
}

# Register completion
complete -F _vit_completion vit
