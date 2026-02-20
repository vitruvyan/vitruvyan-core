"""
Completion command for vit CLI.

Installs/uninstalls bash completion script.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def cmd_completion(args):
    """Install or uninstall bash completion for vit."""
    
    # Get completion script path
    script_dir = Path(__file__).parent.parent / "completion"
    completion_script = script_dir / "vit-completion.bash"
    
    if not completion_script.exists():
        print(f"❌ Completion script not found: {completion_script}")
        return 1
    
    if args.action == "install":
        return install_completion(completion_script, args)
    elif args.action == "uninstall":
        return uninstall_completion(args)
    elif args.action == "show":
        return show_completion(completion_script)
    else:
        print(f"❌ Unknown action: {args.action}")
        return 1


def install_completion(script_path, args):
    """Install completion script."""
    
    # Determine installation location
    if args.system:
        # System-wide installation (requires sudo)
        target_dir = Path("/etc/bash_completion.d")
        target_file = target_dir / "vit"
        
        if not target_dir.exists():
            print(f"❌ System completion directory not found: {target_dir}")
            print("   Try installing bash-completion package:")
            print("   - Ubuntu/Debian: sudo apt install bash-completion")
            print("   - RHEL/CentOS: sudo yum install bash-completion")
            return 1
        
        # Check if we need sudo
        if not os.access(target_dir, os.W_OK):
            print(f"⚠️  Installing to {target_file} requires sudo")
            cmd = ["sudo", "cp", str(script_path), str(target_file)]
            try:
                subprocess.run(cmd, check=True)
                print(f"✅ Completion installed: {target_file}")
                print("\n📝 Restart your shell or run:")
                print(f"   source {target_file}")
                return 0
            except subprocess.CalledProcessError:
                print("❌ Installation failed (sudo required)")
                return 1
        else:
            shutil.copy(script_path, target_file)
            print(f"✅ Completion installed: {target_file}")
            print("\n📝 Restart your shell or run:")
            print(f"   source {target_file}")
            return 0
    
    else:
        # User-level installation
        target_dir = Path.home() / ".bash_completion.d"
        target_file = target_dir / "vit"
        bashrc = Path.home() / ".bashrc"
        
        # Create directory if needed
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy completion script
        shutil.copy(script_path, target_file)
        print(f"✅ Completion installed: {target_file}")
        
        # Check if .bashrc sources completion directory
        bashrc_line = "for f in ~/.bash_completion.d/*; do [ -f \"$f\" ] && source \"$f\"; done"
        
        if bashrc.exists():
            with open(bashrc, "r") as f:
                content = f.read()
            
            if ".bash_completion.d" not in content:
                print("\n📝 Add this to your ~/.bashrc:")
                print(f"   {bashrc_line}")
                
                if not args.no_edit:
                    response = input("\n   Add automatically? [y/N]: ")
                    if response.lower() == "y":
                        with open(bashrc, "a") as f:
                            f.write(f"\n# vit completion\n{bashrc_line}\n")
                        print("   ✅ Added to ~/.bashrc")
            else:
                print("   ℹ️  .bashrc already sources completion directory")
        
        print("\n📝 Restart your shell or run:")
        print(f"   source ~/.bashrc")
        
        return 0


def uninstall_completion(args):
    """Uninstall completion script."""
    
    if args.system:
        target_file = Path("/etc/bash_completion.d/vit")
        
        if not target_file.exists():
            print(f"ℹ️  Completion not installed: {target_file}")
            return 0
        
        # Check if we need sudo
        if not os.access(target_file.parent, os.W_OK):
            print(f"⚠️  Removing {target_file} requires sudo")
            cmd = ["sudo", "rm", str(target_file)]
            try:
                subprocess.run(cmd, check=True)
                print(f"✅ Completion uninstalled: {target_file}")
                return 0
            except subprocess.CalledProcessError:
                print("❌ Uninstallation failed (sudo required)")
                return 1
        else:
            target_file.unlink()
            print(f"✅ Completion uninstalled: {target_file}")
            return 0
    
    else:
        target_file = Path.home() / ".bash_completion.d/vit"
        
        if not target_file.exists():
            print(f"ℹ️  Completion not installed: {target_file}")
            return 0
        
        target_file.unlink()
        print(f"✅ Completion uninstalled: {target_file}")
        print("\n📝 You may want to remove this line from ~/.bashrc:")
        print('   for f in ~/.bash_completion.d/*; do [ -f "$f" ] && source "$f"; done')
        
        return 0


def show_completion(script_path):
    """Show completion script content."""
    
    print(f"📄 Completion script: {script_path}")
    print(f"   Size: {script_path.stat().st_size} bytes\n")
    
    with open(script_path, "r") as f:
        print(f.read())
    
    return 0


def register_completion_command(subparsers):
    """Register the completion command."""
    
    parser = subparsers.add_parser(
        "completion",
        help="Install/uninstall bash completion for vit"
    )
    
    parser.add_argument(
        "action",
        choices=["install", "uninstall", "show"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--system",
        action="store_true",
        help="Install system-wide (requires sudo)"
    )
    
    parser.add_argument(
        "--no-edit",
        action="store_true",
        help="Don't edit .bashrc automatically"
    )
    
    parser.set_defaults(func=cmd_completion)
