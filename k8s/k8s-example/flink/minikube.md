minikube start  --memory=16384 --cpus=12 --disk-size=300g  --no-vtx-check




# minikube VM 있는지 확인
Get-VM minikube

# 있다면 강제 종료
Stop-VM -Name minikube -TurnOff -Force

# 그리고 VM 자체 삭제
Remove-VM -Name minikube -Force


# 혹시 떠있는 minikube 프로세스 강제 종료
taskkill /IM minikube.exe /F 2>$null

# 깨진 머신 폴더 삭제
rmdir "$env:USERPROFILE\.minikube\machines\minikube" /s /q

# 깨진 프로필 폴더 삭제
rmdir "$env:USERPROFILE\.minikube\profiles\minikube" /s /q

del "$env:USERPROFILE\.minikube\config\config.json


# config 추출
kubectl config view --raw --minify --flatten > kubeconfig