#!/bin/bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLUSTER_NAME="${CLUSTER_NAME:-flink-cluster}"
KIND_VERSION="${KIND_VERSION:-v0.23.0}"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

abort() {
  echo "ERROR: $*" >&2
  exit 1
}

ensure_binary() {
  local bin="$1"
  if ! command -v "$bin" >/dev/null 2>&1; then
    return 1
  fi
}

ensure_docker() {
  if ! ensure_binary docker; then
    abort "Docker가 설치되어 있지 않습니다. 먼저 Docker를 설치하세요."
  fi

  if ! docker info >/dev/null 2>&1; then
    abort "Docker가 실행 중이 아닙니다. Docker Desktop을 켜거나 'sudo service docker start' 후 다시 시도하세요."
  fi
}

install_kind() {
  local os arch url tmpfile
  os="$(uname | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"

  case "$arch" in
    x86_64|amd64) arch="amd64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) abort "지원하지 않는 아키텍처입니다: $arch" ;;
  esac

  url="https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-${os}-${arch}"
  tmpfile="$(mktemp)"
  log "kind가 없어 다운로드합니다 (${url})"
  curl -Lo "$tmpfile" "$url"
  chmod +x "$tmpfile"

  if install -m 0755 "$tmpfile" /usr/local/bin/kind 2>/dev/null; then
    log "kind를 /usr/local/bin/kind 에 설치했습니다."
  else
    mkdir -p "${HOME}/.local/bin"
    mv "$tmpfile" "${HOME}/.local/bin/kind"
    chmod +x "${HOME}/.local/bin/kind"
    export PATH="${HOME}/.local/bin:${PATH}"
    log "kind를 ${HOME}/.local/bin/kind 에 설치했습니다. PATH에 ${HOME}/.local/bin 을 추가했습니다."
  fi
}

ensure_kind() {
  if ! ensure_binary kind; then
    install_kind
  fi
}

ensure_helm() {
  if ensure_binary helm; then
    return
  fi
  log "Helm이 없어 설치 스크립트를 실행합니다."
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
}

ensure_kubectl() {
  if ! ensure_binary kubectl; then
    abort "kubectl이 설치되어 있지 않습니다. 먼저 kubectl을 설치하세요."
  fi
}

create_kind_cluster() {
  if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
    log "이미 kind 클러스터가 존재합니다: ${CLUSTER_NAME}"
    return
  fi

  log "kind 클러스터를 생성합니다: ${CLUSTER_NAME}"
  kind create cluster --name "$CLUSTER_NAME"
}

switch_context() {
  local ctx="kind-${CLUSTER_NAME}"
  log "kubectl 컨텍스트를 ${ctx} 로 전환합니다."
  kubectl config use-context "$ctx" >/dev/null
}

run_flink_setup() {
  log "Flink 설치 스크립트를 실행합니다."
  bash "${REPO_DIR}/setup.sh"
}

log "===== 빠른 Flink 설치를 시작합니다 ====="
ensure_docker
ensure_kubectl
ensure_kind
ensure_helm
create_kind_cluster
switch_context
run_flink_setup
log "===== 모든 작업이 완료되었습니다 ====="
log "상태 확인: kubectl get pods -n flink-busan"

