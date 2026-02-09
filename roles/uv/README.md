# uv Role

This Ansible role installs [uv](https://github.com/astral-sh/uv), an extremely fast Python package installer and resolver written in Rust.

## Requirements

- Linux/Unix system (macOS, Linux distributions)
- `curl` or `wget` available on the target system
- Internet connectivity to download the installer

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

```yaml
# Set to '1' to disable modifying PATH in shell profiles during installation
uv_no_modify_path: '0'

# Whether to ensure uv is in PATH by modifying .bashrc
uv_ensure_path: true

# Whether to enable bash completion for uv and uvx commands
uv_enable_completion: false
```

## Dependencies

None.

## Example Playbook

Basic installation:

```yaml
- hosts: servers
  roles:
    - role: uv
```

With custom variables:

```yaml
- hosts: servers
  roles:
    - role: uv
      vars:
        uv_enable_completion: true
        uv_no_modify_path: '0'
```

## Features

- Idempotent installation (checks if uv is already installed)
- Uses the official standalone installer from https://astral.sh/uv/install.sh
- Optionally configures PATH in .bashrc
- Optionally enables bash completion for uv and uvx commands
- Verifies installation after completion

## Upgrading uv

To upgrade uv to the latest version, you can run:

```bash
uv self update
```

Or simply run the playbook again with the role, as it will reinstall if needed.

## Documentation

For more information about uv, visit:
- [Official Documentation](https://docs.astral.sh/uv/)
- [GitHub Repository](https://github.com/astral-sh/uv)

## License

GPL-v3

## Author Information

Created for the NAU platform infrastructure.
