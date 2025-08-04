#!/bin/bash

echo "🚀 블로그 자동화 Docker 환경 시작"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose -f docker-compose.blog.yml down

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose -f docker-compose.blog.yml build

# 컨테이너 시작
echo "▶️ 컨테이너 시작 중..."
docker-compose -f docker-compose.blog.yml up -d

# 로그 확인
echo "📋 컨테이너 로그 확인 중..."
docker-compose -f docker-compose.blog.yml logs -f blog-automation 