#!/usr/bin/env bash
# Bash completion script for vit (Vitruvyan Package Manager)
# Installation: source this file or copy to /etc/bash_completion.d/vit

_vit_completion() {
    local cur prev words cword
    _init_completion || return

    # Commands
    local commands="update upgrade plan rollback status channel completion release help"
    
    # Global flags
    local global_flags="--help --version --verbose --quiet"
    
    # Command-specific flags
    local update_flags="--channel --json"
    local upgrade_flags="--channel --target --yes --json"
    local plan_flags="--target --channel --json"
    local rollback_flags="--yes"
    local status_flags="--json"
    local channel_flags=""
    local completion_flags="install uninstall show --system --no-edit"
    local release_flags="--dry-run"
    
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
        completion)
            COMPREPLY=( $(compgen -W "${completion_flags}" -- "${cur}") )
            return 0
            ;;
        release)
            COMPREPLY=( $(compgen -W "${release_flags}" -- "${cur}") )
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
        completion)
            COMPREPLY=( $(compgen -W "${completion_flags}" -- "${cur}") )
            ;;
        release)
            COMPREPLY=( $(compgen -W "${release_flags}" -- "${cur}") )
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
    
    return 0
}

# Register completion
complete -F _vit_completion vit
