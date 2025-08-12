// 컬럼 리사이즈 기능
class ColumnResizer {
    constructor(tableId) {
        this.table = document.getElementById(tableId);
        this.isResizing = false;
        this.currentColumn = null;
        this.startX = 0;
        this.startWidth = 0;
        this.minWidth = 180; // 최소 너비
        this.animationFrameId = null;
        this.resizeTimeout = null;
        this.columnWidths = new Map(); // 컬럼별 너비 저장
        
        this.init();
    }
    
    init() {
        if (!this.table) {
            console.error('테이블을 찾을 수 없습니다:', this.table);
            return;
        }
        
        // 테이블 헤더에 리사이즈 핸들 추가
        this.addResizeHandles();
        
        // 이벤트 리스너 등록
        this.bindEvents();
        
        // 서버에서 저장된 컬럼 너비 먼저 불러오기
        this.loadServerColumnWidths();
        
        // 저장된 컬럼 너비 복원 (localStorage)
        this.restoreColumnWidths();
    }
    
    // 저장된 컬럼 너비 복원
    restoreColumnWidths() {
        const userId = getCurrentUserId();
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (header.classList.contains('add-attribute-th')) return;
            
            const attrName = header.getAttribute('data-column');
            if (attrName) {
                const savedWidth = localStorage.getItem(`column_width_${attrName}_${userId}`);
                const savedMaxWidth = localStorage.getItem(`column_max_width_${attrName}_${userId}`);
                const dataWidth = header.getAttribute('data-width');
                
                // 우선순위: localStorage > data-width > 기본값
                let width = null;
                if (savedWidth) {
                    width = parseInt(savedWidth);
                } else if (dataWidth) {
                    width = parseInt(dataWidth);
                }
                
                if (width) {
                    // 헤더에 너비 적용
                    header.style.width = width + 'px';
                    header.style.minWidth = width + 'px';
                    header.style.maxWidth = width + 'px';
                    
                    // 셀에도 너비 적용
                    const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
                    cells.forEach(cell => {
                        cell.style.width = width + 'px';
                        cell.style.minWidth = width + 'px';
                        cell.style.maxWidth = width + 'px';
                        cell.style.overflow = 'hidden';
                        cell.style.textOverflow = 'ellipsis';
                        cell.style.whiteSpace = 'nowrap';
                    });
                    
                }
                
                // 최대 너비도 복원
                if (savedMaxWidth) {
                    this.applyColumnMaxWidth(attrName, parseInt(savedMaxWidth));
                }
            }
        });
    }
    
    // 컬럼 최대 너비 적용
    applyColumnMaxWidth(attrName, maxWidth) {
        const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
        cells.forEach(cell => {
            cell.style.maxWidth = maxWidth + 'px';
            cell.style.overflow = 'hidden';
            cell.style.textOverflow = 'ellipsis';
            cell.style.whiteSpace = 'nowrap';
        });
    }
    
    // 컬럼 최대 너비 계산 (컬럼 너비에 비례)
    calculateColumnMaxWidth(width) {
        // 컬럼 너비에 비례하여 최대 너비 계산 (예: 컬럼 너비의 0.8배)
        const maxWidth = Math.max(width * 0.8, 50); // 최소 50px
        return Math.round(maxWidth);
    }
    
    addResizeHandles() {
        const headers = this.table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            // 마지막 열(속성 추가 열)은 제외
            if (header.classList.contains('add-attribute-th')) {
                console.log('속성 추가 열 제외:', index);
                return;
            }
            
            // 리사이즈 핸들 생성
            const handle = document.createElement('div');
            handle.className = 'column-resize-handle';
            handle.style.cssText = `
                position: absolute;
                right: -3px;
                top: 0;
                bottom: 0;
                width: 6px;
                cursor: col-resize;
                background: transparent;
                z-index: 10;
                transition: background-color 0.2s ease, opacity 0.2s ease;
            `;
            
            // 헤더에 상대 위치 설정
            header.style.position = 'relative';
            header.appendChild(handle);
            
            // 마우스 오버 시 핸들 표시 (디바운싱 적용)
            let hoverTimeout;
            header.addEventListener('mouseenter', () => {
                if (!this.isResizing) {
                    clearTimeout(hoverTimeout);
                    hoverTimeout = setTimeout(() => {
                        handle.style.background = '#007bff';
                        handle.style.opacity = '0.3';
                    }, 50);
                }
            });
            
            header.addEventListener('mouseleave', () => {
                if (!this.isResizing) {
                    clearTimeout(hoverTimeout);
                    hoverTimeout = setTimeout(() => {
                        handle.style.background = 'transparent';
                        handle.style.opacity = '0';
                    }, 100);
                }
            });
        });
    }
    
    bindEvents() {
        // 마우스 다운 이벤트
        document.addEventListener('mousedown', (e) => {
            const handle = e.target.closest('.column-resize-handle');
            if (!handle) return;
            
            e.preventDefault();
            e.stopPropagation();
            this.startResize(e, handle);
        });
        
        // 마우스 이동 이벤트 (requestAnimationFrame 사용)
        document.addEventListener('mousemove', (e) => {
            if (!this.isResizing) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            // 이전 애니메이션 프레임 취소
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
            }
            
            // requestAnimationFrame으로 부드러운 리사이즈
            this.animationFrameId = requestAnimationFrame(() => {
                this.resize(e);
            });
        });
        
        // 마우스 업 이벤트
        document.addEventListener('mouseup', (e) => {
            if (this.isResizing) {
                console.log('리사이즈 종료');
                e.preventDefault();
                e.stopPropagation();
                this.stopResize();
            }
        });
        
        // ESC 키로 리사이즈 취소
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isResizing) {
                this.cancelResize();
            }
        });
        console.log('이벤트 바인딩 완료');
    }
    
    startResize(e, handle) {
        console.log('startResize 함수 호출됨');
        this.isResizing = true;
        this.currentColumn = handle.closest('th');
        this.startX = e.clientX;
        this.startWidth = this.currentColumn.offsetWidth;
        
        // 테이블 레이아웃을 fixed로 변경하여 컬럼 너비 고정
        this.table.style.tableLayout = 'fixed';
        
        // 테이블에 리사이징 클래스 추가 (CSS 최적화)
        this.table.classList.add('resizing');
        
        // 현재 컬럼의 CSS 제한 해제 (성능 최적화)
        this.currentColumn.style.width = this.startWidth + 'px';
        this.currentColumn.style.minWidth = this.startWidth + 'px';
        this.currentColumn.style.maxWidth = 'none';
        
        // 리사이즈 중임을 표시
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        // 현재 컬럼에 리사이징 클래스 추가
        this.currentColumn.classList.add('resizing');
        
        // 핸들 스타일 변경
        handle.style.background = '#007bff';
        handle.style.opacity = '1';
        
        // 가이드 라인 추가
        this.addGuideLine();
        console.log('startResize 완료');
    }
    
    resize(e) {
        if (!this.currentColumn) return;
        
        const deltaX = e.clientX - this.startX;
        const newWidth = Math.max(this.startWidth + deltaX, this.minWidth);
        
        // 컬럼 너비 설정 (성능 최적화 - !important 제거)
        this.currentColumn.style.width = newWidth + 'px';
        this.currentColumn.style.minWidth = newWidth + 'px';
        this.currentColumn.style.maxWidth = newWidth + 'px';
        
        // 컬럼 최대 너비 계산 및 적용
        const newMaxWidth = this.calculateColumnMaxWidth(newWidth);
        this.applyColumnMaxWidth(this.currentColumn.getAttribute('data-column'), newMaxWidth);
        
        // 제목 자동 조정을 위한 이벤트 발생
        this.currentColumn.dispatchEvent(new CustomEvent('columnResized', {
            detail: { width: newWidth }
        }));
        
        // 가이드 라인 위치 업데이트
        this.updateGuideLine(newWidth);
    }
    
    stopResize() {
        if (!this.currentColumn) return;
        
        this.isResizing = false;
        
        // 애니메이션 프레임 취소
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        
        // 리사이징 클래스 제거
        this.currentColumn.classList.remove('resizing');
        
        // 테이블 리사이징 클래스 제거
        this.table.classList.remove('resizing');
        
        // 테이블 레이아웃 복원
        this.table.style.tableLayout = 'auto';
        
        // width와 height 저장 (디바운싱 적용)
        const attrName = this.currentColumn.getAttribute('data-column');
        const width = parseInt(this.currentColumn.offsetWidth, 10);
        const maxWidth = this.calculateColumnMaxWidth(width);
        
        if (attrName && width) {
            // 헤더에 최종 너비 적용
            this.currentColumn.style.width = width + 'px';
            this.currentColumn.style.minWidth = width + 'px';
            this.currentColumn.style.maxWidth = width + 'px';
            
            // 셀에도 너비 적용
            const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
            cells.forEach(cell => {
                cell.style.width = width + 'px';
                cell.style.minWidth = width + 'px';
                cell.style.maxWidth = width + 'px';
                cell.style.overflow = 'hidden';
                cell.style.textOverflow = 'ellipsis';
                cell.style.whiteSpace = 'nowrap';
            });
            
            // 이전 타임아웃 취소
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }
            
            // 디바운싱으로 저장 지연
            this.resizeTimeout = setTimeout(() => {
                this.saveColumnWidth(attrName, width, maxWidth);
            }, 300);
        }
        
        this.currentColumn = null;
        
        // 스타일 복원
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        // 가이드 라인 제거
        this.removeGuideLine();
        
        // 모든 핸들 스타일 복원
        const handles = document.querySelectorAll('.column-resize-handle');
        handles.forEach(handle => {
            handle.style.background = 'transparent';
            handle.style.opacity = '0';
        });
    }
    
    saveColumnWidth(attrName, width, maxWidth) {
        // 서버에 너비 저장
        fetch('/sales/save_column_width/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/)||[])[1] || ''
            },
            body: JSON.stringify({ attribute_name: attrName, width: width })
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                console.error('컬럼 너비 저장 실패:', data.error);
            } else {
                console.log('컬럼 너비 저장 성공:', data.message);
            }
        })
        .catch(err => console.error('컬럼 너비 저장 오류:', err));
        
        // 로컬 스토리지에 너비 저장 (사용자별)
        const userId = getCurrentUserId();
        localStorage.setItem(`column_width_${attrName}_${userId}`, width.toString());
        localStorage.setItem(`column_max_width_${attrName}_${userId}`, maxWidth.toString());
        console.log(`컬럼 너비 저장: ${attrName} = ${width}px, 최대 너비 = ${maxWidth}px (사용자: ${userId})`);
    }
    
    cancelResize() {
        if (!this.currentColumn) return;
        
        // 원래 너비로 복원
        this.currentColumn.style.width = this.startWidth + 'px';
        this.currentColumn.style.minWidth = this.startWidth + 'px';
        this.currentColumn.style.maxWidth = 'none';
        
        // 원래 높이로 복원
        const attrName = this.currentColumn.getAttribute('data-column');
        if (attrName) {
            const originalMaxWidth = this.calculateColumnMaxWidth(this.startWidth);
            this.applyColumnMaxWidth(attrName, originalMaxWidth);
        }
        
        // 테이블 리사이징 클래스 제거
        this.table.classList.remove('resizing');
        
        this.stopResize();
    }
    
    addGuideLine() {
        const guideLine = document.createElement('div');
        guideLine.id = 'column-resize-guide';
        guideLine.style.cssText = `
            position: fixed;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #007bff;
            z-index: 10000;
            pointer-events: none;
            transform: translateZ(0);
        `;
        document.body.appendChild(guideLine);
    }
    
    updateGuideLine(width) {
        const guideLine = document.getElementById('column-resize-guide');
        if (guideLine && this.currentColumn) {
            const rect = this.currentColumn.getBoundingClientRect();
            guideLine.style.left = (rect.left + width) + 'px';
        }
    }
    
    removeGuideLine() {
        const guideLine = document.getElementById('column-resize-guide');
        if (guideLine) {
            guideLine.remove();
        }
    }
    
    // 정리 함수
    destroy() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        this.removeGuideLine();
        
        // 테이블 리사이징 클래스 제거
        if (this.table) {
            this.table.classList.remove('resizing');
        }
    }
    
    // 저장된 컬럼 너비 로드 함수
    loadColumnWidths() {
        const userId = getCurrentUserId();
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (header.classList.contains('add-attribute-th')) return;
            
            const attrName = header.getAttribute('data-column');
            if (attrName) {
                const savedWidth = localStorage.getItem(`column_width_${attrName}_${userId}`);
                const savedMaxWidth = localStorage.getItem(`column_max_width_${attrName}_${userId}`);
                const dataWidth = header.getAttribute('data-width');
                
                // 우선순위: localStorage > data-width > 기본값
                let width = null;
                if (savedWidth) {
                    width = parseInt(savedWidth);
                    console.log(`localStorage에서 너비 로드: ${attrName} = ${width}px (사용자: ${userId})`);
                } else if (dataWidth) {
                    width = parseInt(dataWidth);
                    console.log(`data-width에서 너비 적용: ${attrName} = ${width}px`);
                }
                
                if (width) {
                    // 헤더에 너비 적용
                    header.style.width = width + 'px';
                    header.style.minWidth = width + 'px';
                    header.style.maxWidth = width + 'px';
                    
                    // 셀에도 너비 적용
                    const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
                    cells.forEach(cell => {
                        cell.style.width = width + 'px';
                        cell.style.minWidth = width + 'px';
                        cell.style.maxWidth = width + 'px';
                        cell.style.overflow = 'hidden';
                        cell.style.textOverflow = 'ellipsis';
                        cell.style.whiteSpace = 'nowrap';
                    });
                    
                    console.log(`컬럼 너비 적용: ${attrName} = ${width}px`);
                }
                
                // 최대 너비도 복원
                if (savedMaxWidth) {
                    const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
                    cells.forEach(cell => {
                        cell.style.maxWidth = savedMaxWidth + 'px';
                        cell.style.overflow = 'hidden';
                        cell.style.textOverflow = 'ellipsis';
                        cell.style.whiteSpace = 'nowrap';
                    });
                    console.log(`max-width 복원: ${attrName} = ${savedMaxWidth}px`);
                }
            }
        });
    }
    
    // 서버에서 저장된 컬럼 너비 불러오기
    loadServerColumnWidths() {
        fetch('/sales/get_column_widths/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/)||[])[1] || ''
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.widths) {
                console.log('서버에서 컬럼 너비 로드:', data.widths);
                const userId = getCurrentUserId();
                
                // 서버에서 가져온 너비를 localStorage에 저장하고 적용
                Object.entries(data.widths).forEach(([attrName, width]) => {
                    localStorage.setItem(`column_width_${attrName}_${userId}`, width.toString());
                    
                    // 테이블에 너비 적용
                    const header = this.table.querySelector(`th[data-column="${attrName}"]`);
                    if (header) {
                        header.style.width = width + 'px';
                        header.style.minWidth = width + 'px';
                        header.style.maxWidth = width + 'px';
                        
                        // 셀에도 너비 적용
                        const cells = this.table.querySelectorAll(`td[data-field="${attrName}"]`);
                        cells.forEach(cell => {
                            cell.style.width = width + 'px';
                            cell.style.minWidth = width + 'px';
                            cell.style.maxWidth = width + 'px';
                            cell.style.overflow = 'hidden';
                            cell.style.textOverflow = 'ellipsis';
                            cell.style.whiteSpace = 'nowrap';
                        });
                        
                    }
                });
            } else {
                console.log('서버에서 저장된 컬럼 너비가 없습니다.');
            }
        })
        .catch(err => {
            console.error('서버에서 컬럼 너비 로드 오류:', err);
        });
    }
}

// 페이지 로드 시 컬럼 리사이저 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded 이벤트 발생');
    // 테이블이 로드된 후 리사이저 초기화
    setTimeout(() => {
        console.log('리사이저 초기화 시도');
        const table = document.getElementById('entryTable');
        console.log('찾은 테이블:', table);
        if (table) {
            // 기존 리사이저 정리
            if (window.columnResizer) {
                window.columnResizer.destroy();
            }
            window.columnResizer = new ColumnResizer('entryTable');
        } else {
            console.error('entryTable을 찾을 수 없습니다');
        }
    }, 500);
});

// 테이블 새로고침 후 리사이저 재초기화 함수
function reinitializeColumnResizer() {
    // 기존 리사이저 정리
    if (window.columnResizer) {
        window.columnResizer.destroy();
    }
    
    // 기존 핸들들 제거
    const handles = document.querySelectorAll('.column-resize-handle');
    handles.forEach(handle => handle.remove());
    
    // 새로운 리사이저 초기화
    setTimeout(() => {
        const table = document.getElementById('entryTable');
        if (table) {
            window.columnResizer = new ColumnResizer('entryTable');
            
            // 서버에서 저장된 너비 먼저 불러오기
            window.columnResizer.loadServerColumnWidths();
            
            // 저장된 너비 즉시 적용 (localStorage)
            const userId = getCurrentUserId();
            const headers = table.querySelectorAll('thead th');
            headers.forEach((header, index) => {
                if (header.classList.contains('add-attribute-th')) return;
                
                const attrName = header.getAttribute('data-column');
                if (attrName) {
                    const savedWidth = localStorage.getItem(`column_width_${attrName}_${userId}`);
                    if (savedWidth) {
                        const width = parseInt(savedWidth);
                        // 헤더에 너비 적용
                        header.style.width = width + 'px';
                        header.style.minWidth = width + 'px';
                        header.style.maxWidth = width + 'px';
                        
                        // 셀에도 너비 적용
                        const cells = table.querySelectorAll(`td[data-field="${attrName}"]`);
                        cells.forEach(cell => {
                            cell.style.width = width + 'px';
                            cell.style.minWidth = width + 'px';
                            cell.style.maxWidth = width + 'px';
                            cell.style.overflow = 'hidden';
                            cell.style.textOverflow = 'ellipsis';
                            cell.style.whiteSpace = 'nowrap';
                        });
                        
                    }
                }
            });
        }
    }, 100);
}