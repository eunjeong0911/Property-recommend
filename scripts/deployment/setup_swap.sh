#!/bin/bash

# =============================================================================
# Swap Memory Setup Script for t3.small
# =============================================================================
# 이 스크립트는 2GB RAM을 가진 t3.small 인스턴스에서 OOM(Out of Memory)을 방지하기 위해
# 4GB의 스왑 파일을 생성하고 활성화합니다.
#
# Usage: sudo ./setup_swap.sh
# =============================================================================

# 스왑 파일 크기 (4GB)
SWAP_SIZE=4G
SWAP_FILE=/swapfile

echo "Initializing Swap Setup..."

# 1. 기존 스왑 확인
if grep -q "swap" /etc/fstab; then
    echo "Swap file is already configured in /etc/fstab."
    free -h
    exit 0
fi

# 2. 스왑 파일 생성
echo "Creating $SWAP_SIZE swap file at $SWAP_FILE..."
sudo fallocate -l $SWAP_SIZE $SWAP_FILE
# fallocate 실패 시 dd 사용 (호환성)
if [ $? -ne 0 ]; then
    echo "fallocate failed, using dd..."
    sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=4096
fi

# 3. 권한 설정 (600 - root만 읽기/쓰기 가능)
echo "Setting permissions..."
sudo chmod 600 $SWAP_FILE

# 4. 스왑 영역 설정
echo "Setting up swap area..."
sudo mkswap $SWAP_FILE

# 5. 스왑 활성화
echo "Enabling swap..."
sudo swapon $SWAP_FILE

# 6. 재부팅 시 자동 마운트 설정 (/etc/fstab 추가)
echo "Updating /etc/fstab..."
echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab

# 7. 설정 확인
echo "Swap setup complete!"
free -h
