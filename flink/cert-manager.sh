#!/bin/bash

# cert-manager 설치 스크립트
# Kubernetes에서 TLS 인증서를 자동으로 관리하기 위한 cert-manager를 설치합니다.
# Flink Operator가 TLS 인증서를 사용할 때 필요합니다.

set -euo pipefail

kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.18.2/cert-manager.yaml