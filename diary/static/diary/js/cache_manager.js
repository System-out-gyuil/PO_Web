/**
 * Entry Table Partial 캐시 관리자
 * 테이블 리랜더링 시 최신 데이터를 보장합니다.
 */

class EntryTableCacheManager {
    constructor() {
        this.cacheTimestamp = null;
        this.currentStatusId = 'all';
        this.isRefreshing = false;
    }

    /**
     * 테이블을 새로고침합니다 (캐시 무시)
     */
    async forceRefresh() {
        try {
            this.isRefreshing = true;
            
            // 서버에서 모든 캐시 무효화
            const response = await fetch('/force_refresh_entry_table/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('캐시 강제 무효화 완료:', result.message);
                this.cacheTimestamp = result.new_timestamp;
                
                // 테이블 새로고침
                await this.refreshTable();
                return true;
            } else {
                console.error('캐시 무효화 실패:', result.error);
                return false;
            }
        } catch (error) {
            console.error('강제 새로고침 중 오류:', error);
            return false;
        } finally {
            this.isRefreshing = false;
        }
    }

    /**
     * 특정 상태의 테이블을 새로고침합니다
     */
    async refreshTable(statusId = null) {
        if (this.isRefreshing) {
            console.log('이미 새로고침 중입니다.');
            return false;
        }

        try {
            this.isRefreshing = true;
            
            if (statusId) {
                this.currentStatusId = statusId;
            }
            
            // no_cache=1 파라미터로 캐시 무시
            const url = `/entry_table_partial/?status_id=${this.currentStatusId}&no_cache=1&cache_timestamp=${this.cacheTimestamp || ''}`;
            
            const response = await fetch(url);
            if (response.ok) {
                const html = await response.text();
                
                // 테이블 컨테이너 찾기 및 업데이트
                const tableContainer = document.querySelector('#entry-table-container') || 
                                    document.querySelector('.entry-table') ||
                                    document.querySelector('[data-entry-table]');
                
                if (tableContainer) {
                    tableContainer.innerHTML = html;
                    console.log('테이블 새로고침 완료');
                    
                    // 새로운 캐시 타임스탬프 추출
                    this.extractCacheTimestamp(html);
                    
                    // 이벤트 리스너 재등록
                    this.reattachEventListeners();
                    return true;
                } else {
                    console.error('테이블 컨테이너를 찾을 수 없습니다.');
                    return false;
                }
            } else {
                console.error('테이블 새로고침 실패:', response.status);
                return false;
            }
        } catch (error) {
            console.error('테이블 새로고침 중 오류:', error);
            return false;
        } finally {
            this.isRefreshing = false;
        }
    }

    /**
     * 최신 데이터를 직접 가져와서 테이블을 업데이트합니다
     */
    async updateTableWithLatestData(statusId = null) {
        try {
            if (statusId) {
                this.currentStatusId = statusId;
            }
            
            const response = await fetch(`/get_entry_table_data/?status_id=${this.currentStatusId}`);
            const result = await response.json();
            
            if (result.success) {
                // 새로운 캐시 타임스탬프 저장
                this.cacheTimestamp = result.cache_timestamp;
                
                // 테이블 데이터로 HTML 생성 (템플릿이 필요한 경우)
                const tableHtml = this.generateTableHtml(result.data);
                
                // 테이블 업데이트
                const tableContainer = document.querySelector('#entry-table-container') || 
                                    document.querySelector('.entry-table') ||
                                    document.querySelector('[data-entry-table]');
                
                if (tableContainer) {
                    tableContainer.innerHTML = tableHtml;
                    console.log('최신 데이터로 테이블 업데이트 완료');
                    
                    // 이벤트 리스너 재등록
                    this.reattachEventListeners();
                    return true;
                }
            } else {
                console.error('최신 데이터 조회 실패:', result.error);
            }
        } catch (error) {
            console.error('최신 데이터 업데이트 중 오류:', error);
        }
        return false;
    }

    /**
     * 캐시 상태를 확인합니다
     */
    async getCacheStatus() {
        try {
            const response = await fetch('/get_cache_status/');
            const result = await response.json();
            
            if (result.success) {
                console.log('캐시 상태:', result.cache_info);
                return result.cache_info;
            } else {
                console.error('캐시 상태 조회 실패:', result.error);
                return null;
            }
        } catch (error) {
            console.error('캐시 상태 조회 중 오류:', error);
            return null;
        }
    }

    /**
     * 특정 상태의 캐시를 무효화합니다
     */
    async invalidateCache(statusId = 'all') {
        try {
            const response = await fetch('/invalidate_entry_table_cache/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ status_id: statusId })
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('캐시 무효화 완료:', result.message);
                return true;
            } else {
                console.error('캐시 무효화 실패:', result.error);
                return false;
            }
        } catch (error) {
            console.error('캐시 무효화 중 오류:', error);
            return false;
        }
    }

    /**
     * HTML에서 캐시 타임스탬프를 추출합니다
     */
    extractCacheTimestamp(html) {
        try {
            // HTML에서 data-cache-timestamp 속성이나 숨겨진 필드에서 추출
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            const timestampElement = tempDiv.querySelector('[data-cache-timestamp]') ||
                                  tempDiv.querySelector('input[name="cache_timestamp"]') ||
                                  tempDiv.querySelector('.cache-timestamp');
            
            if (timestampElement) {
                this.cacheTimestamp = timestampElement.value || timestampElement.textContent || timestampElement.dataset.cacheTimestamp;
                console.log('캐시 타임스탬프 추출:', this.cacheTimestamp);
            }
        } catch (error) {
            console.error('캐시 타임스탬프 추출 중 오류:', error);
        }
    }

    /**
     * 테이블 HTML을 생성합니다 (템플릿이 필요한 경우)
     */
    generateTableHtml(data) {
        // 기본적인 테이블 HTML 생성
        // 실제 구현에서는 Django 템플릿이나 더 정교한 HTML 생성 로직이 필요할 수 있습니다
        let html = '<div class="entry-table" data-cache-timestamp="' + data.cache_timestamp + '">';
        
        // 속성 헤더
        html += '<div class="table-header">';
        data.attributes.forEach(attr => {
            html += '<div class="header-cell">' + attr.name + '</div>';
        });
        html += '</div>';
        
        // 행 데이터
        data.rows.forEach(row => {
            html += '<div class="table-row" data-row-id="' + row.id + '">';
            data.attributes.forEach(attr => {
                const value = row.values[attr.name] || '';
                const displayValue = value.label || value || '';
                html += '<div class="table-cell">' + displayValue + '</div>';
            });
            html += '</div>';
        });
        
        html += '</div>';
        return html;
    }

    /**
     * 이벤트 리스너를 재등록합니다
     */
    reattachEventListeners() {
        // 테이블 내의 클릭 이벤트, 편집 이벤트 등을 재등록
        // 실제 구현에서는 필요한 이벤트 리스너들을 여기에 추가
        
        // 예: 행 클릭 이벤트
        const rows = document.querySelectorAll('.table-row');
        rows.forEach(row => {
            row.addEventListener('click', (e) => {
                const rowId = row.dataset.rowId;
                console.log('행 클릭:', rowId);
                // 필요한 행 클릭 처리 로직
            });
        });
        
        console.log('이벤트 리스너 재등록 완료');
    }

    /**
     * CSRF 토큰을 가져옵니다
     */
    getCsrfToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }

    /**
     * 주기적으로 테이블을 새로고침합니다
     */
    startAutoRefresh(intervalMs = 30000) { // 기본 30초
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.autoRefreshInterval = setInterval(() => {
            console.log('자동 새로고침 실행');
            this.refreshTable();
        }, intervalMs);
        
        console.log(`자동 새로고침 시작 (${intervalMs/1000}초 간격)`);
    }

    /**
     * 자동 새로고침을 중지합니다
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('자동 새로고침 중지');
        }
    }
}

// 전역 인스턴스 생성
window.entryTableCacheManager = new EntryTableCacheManager();

// 사용 예시:
// 1. 강제 새로고침: window.entryTableCacheManager.forceRefresh()
// 2. 특정 상태 새로고침: window.entryTableCacheManager.refreshTable('5')
// 3. 최신 데이터로 업데이트: window.entryTableCacheManager.updateTableWithLatestData()
// 4. 캐시 상태 확인: window.entryTableCacheManager.getCacheStatus()
// 5. 자동 새로고침 시작: window.entryTableCacheManager.startAutoRefresh(60000) // 1분 간격
// 6. 자동 새로고침 중지: window.entryTableCacheManager.stopAutoRefresh() 