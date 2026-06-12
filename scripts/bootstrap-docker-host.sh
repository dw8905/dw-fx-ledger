#!/usr/bin/env bash
set -euo pipefail

is_wsl() {
  grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

require_ubuntu_like_host() {
  if [[ ! -r /etc/os-release ]]; then
    echo "Cannot detect OS. This bootstrap script supports Ubuntu/WSL hosts."
    exit 1
  fi

  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" && "${ID_LIKE:-}" != *"debian"* ]]; then
    echo "Unsupported OS: ${PRETTY_NAME:-unknown}"
    echo "Install Docker manually, then run: bash scripts/docker-dev-up.sh"
    exit 1
  fi
}

confirm() {
  local prompt="$1"
  local answer

  read -r -p "$prompt [y/N] " answer
  [[ "$answer" == "y" || "$answer" == "Y" ]]
}

handle_docker_permission_denied() {
  echo
  echo "Docker daemon is reachable, but the current user cannot access it."
  echo "To allow docker commands without sudo:"
  echo "  sudo usermod -aG docker $USER"
  echo "Then close and reopen the WSL shell."

  if confirm "Add '$USER' to the docker group now?"; then
    sudo usermod -aG docker "$USER"
    echo
    echo "User '$USER' was added to the docker group."
    echo "Close and reopen the WSL shell, then rerun:"
    echo "  bash scripts/docker-dev-up.sh"
  fi

  exit 1
}

print_status() {
  echo
  echo "Host checks:"
  if has_command git; then
    echo "  git: $(git --version)"
  else
    echo "  git: not found"
  fi

  if has_command docker; then
    echo "  docker: $(docker --version)"
  else
    echo "  docker: not found"
  fi

  if docker compose version >/dev/null 2>&1; then
    echo "  docker compose: $(docker compose version)"
  else
    echo "  docker compose: not available"
  fi
}

install_docker_engine() {
  require_ubuntu_like_host

  echo "Installing Docker Engine and Docker Compose plugin..."
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  . /etc/os-release
  local codename="${VERSION_CODENAME:-}"
  if [[ -z "$codename" ]]; then
    codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-}")"
  fi
  if [[ -z "$codename" ]]; then
    echo "Cannot detect Ubuntu codename for Docker apt repository."
    exit 1
  fi

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${codename} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

ensure_git() {
  if has_command git; then
    return
  fi

  if confirm "git is not installed. Install git with apt?"; then
    require_ubuntu_like_host
    sudo apt-get update
    sudo apt-get install -y git
  else
    echo "git is required. Install it and rerun this script."
    exit 1
  fi
}

ensure_docker() {
  if has_command docker && docker compose version >/dev/null 2>&1; then
    return
  fi

  echo
  echo "Docker Engine or Docker Compose plugin is missing."
  if confirm "Install Docker Engine for Ubuntu/WSL now?"; then
    install_docker_engine
  else
    echo "Docker is required. Install it and rerun this script."
    exit 1
  fi
}

ensure_docker_daemon() {
  local docker_info_output

  if docker_info_output="$(docker info 2>&1 >/dev/null)"; then
    return
  fi

  if grep -qiE "permission denied|got permission denied|access denied" <<< "$docker_info_output"; then
    handle_docker_permission_denied
  fi

  echo
  echo "Docker is installed, but the daemon is not reachable."
  if is_wsl; then
    echo "If you use Docker Desktop, enable WSL integration for this distro."
  fi
  echo "If you use Docker Engine inside WSL, try:"
  echo "  sudo service docker start"

  if confirm "Run 'sudo service docker start' now?"; then
    sudo service docker start
  fi

  if docker_info_output="$(docker info 2>&1 >/dev/null)"; then
    return
  fi

  if grep -qiE "permission denied|got permission denied|access denied" <<< "$docker_info_output"; then
    handle_docker_permission_denied
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is still not reachable."
    echo "Fix Docker service/WSL integration, then rerun this script."
    exit 1
  fi
}

ensure_docker_group_hint() {
  if docker ps >/dev/null 2>&1; then
    return
  fi

  echo
  echo "Docker works with sudo, but the current user may not have docker group access."
  echo "To allow docker commands without sudo:"
  echo "  sudo usermod -aG docker $USER"
  echo "Then close and reopen the WSL shell."
}

main() {
  echo "DW FX Ledger Docker host bootstrap"
  print_status

  ensure_git
  ensure_docker
  ensure_docker_daemon
  ensure_docker_group_hint

  echo
  echo "Bootstrap complete."
  echo
  echo "Next steps:"
  echo "  cp .env.docker.example .env.docker.local"
  echo "  vi .env.docker.local"
  echo "  bash scripts/docker-dev-up.sh"
}

main "$@"
