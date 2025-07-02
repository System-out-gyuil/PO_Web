function bindKanbanSortable() {
  document.querySelectorAll('.board-cards').forEach(function(col){
      new Sortable(col, {
          group: 'kanban',
          animation: 150,
          onAdd: function(evt){
              const entryId = evt.item.getAttribute('data-entry-id');
              const newStatusId = col.parentElement.getAttribute('data-status-id');
              const currentKanbanAttr = col.parentElement.getAttribute('data-attr-name') || window.SELECTED_KANBAN_ATTR;
              
              fetch('/diary/update_row_field/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'id='+entryId+'&field='+encodeURIComponent(currentKanbanAttr)+'&value='+encodeURIComponent(newStatusId)
              }).then(()=>{ 
                  refreshKanban(); 
                  refreshTable(); 
                  // 캘린더도 새로고침 (영업진행 변경 시에도 F/U 일정이 관련될 수 있음)
                  if (window.calendar) {
                      window.calendar.refetchEvents();
                  }
              });
          }
      });
  });
  // 칸반 카드 클릭 시 상세 모달
  document.querySelectorAll('.board-card').forEach(function(card){
      card.onclick = function(e) {
          const entryId = card.getAttribute('data-entry-id');
          if(entryId) {
              // 새로운 Row 시스템의 get_row_details 엔드포인트 사용
              fetch('/diary/get_row_details/'+entryId+'/')
                .then(r=>r.json())
                .then(function(data){
                    if(data.success) showDetailModal(data.row_data, data.row_id);
                    else alert('상세정보 불러오기 실패: '+(data.error||''));
                });
          }
      };
  });
  // 새 카드 추가 버튼 이벤트
  document.querySelectorAll('.add-card-btn').forEach(function(btn){
      btn.onclick = function() {
          const statusId = btn.closest('.board-col').getAttribute('data-status-id');
          const currentKanbanAttr = btn.closest('.board-col').getAttribute('data-attr-name') || window.SELECTED_KANBAN_ATTR;
          
          // 새 행 생성 - 선택된 칸반 속성 필드를 해당 컬럼의 상태로 설정
          fetch('/diary/create_new_row/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'field='+encodeURIComponent(currentKanbanAttr)+'&value='+encodeURIComponent(statusId)
          }).then(function(response) {
              return response.json();
          }).then(function(data) {
              if (data.success && data.id) {
                  // 칸반보드와 테이블 새로고침
                  refreshKanban();
                  refreshTable();
              } else {
                  alert('새 카드 생성 실패: ' + (data.error || ''));
              }
          }).catch(function(error) {
              console.error('새 카드 생성 중 오류:', error);
              alert('새 카드 생성 중 오류 발생: ' + error.message);
          });
      };
  });
}

// 칸반보드 필터 기능 추가
function updateKanbanBoard(attrName) {
  const loadingIndicator = document.getElementById('kanbanLoadingIndicator');
  const boardView = document.getElementById('boardView');
  
  // 로딩 표시
  loadingIndicator.style.display = 'block';
  
  fetch('/diary/get_kanban_data/?attr_name=' + encodeURIComponent(attrName))
      .then(response => response.json())
      .then(data => {
          loadingIndicator.style.display = 'none';
          
          if (data.success) {
              // 칸반보드 HTML 생성
              let boardHTML = '<div class="board-container">';
              
              data.board.forEach(function(col) {
                  let colStyle = '';
                  if (col.status.color) {
                      colStyle = `background:${hexToRgba(col.status.color, 0.10)};`;
                  }
                  
                  let titleStyle = '';
                  if (col.status.color) {
                      titleStyle = `background:${hexToRgba(col.status.color, 0.18)};border-left:6px solid ${col.status.color};padding-left:10px;`;
                  } else {
                      titleStyle = 'border-left:6px solid #007bff;padding-left:10px;';
                  }
                  
                  boardHTML += `
                      <div class="board-col" data-status-id="${col.status.id}" data-attr-name="${attrName}" style="${colStyle}">
                          <div class="board-col-title" style="${titleStyle}">${col.status.name}</div>
                          <div class="board-cards">
                  `;
                  
                  col.entries.forEach(function(entry) {
                      const entryName = entry.name || '(이름 없음)';
                      const entryAmount = entry.amount ? `₩${entry.amount}` : '';
                      
                      boardHTML += `
                          <div class="board-card" data-entry-id="${entry.id}">
                              <div class="board-card-title">${entryName}</div>
                              <div class="board-card-amount">${entryAmount}</div>
                          </div>
                      `;
                  });
                  
                  boardHTML += `
                          </div>
                          <button class="add-card-btn" style="display:none;"></button>
                      </div>
                  `;
              });
              
              boardHTML += '</div>';
              
              // 기존 보드 교체
              boardView.innerHTML = boardHTML;
              
              // 이벤트 바인딩 재설정
              bindKanbanSortable();
              
              // 전역 변수 업데이트
              window.SELECTED_KANBAN_ATTR = attrName;
              
          } else {
              alert('칸반보드 데이터를 불러오는데 실패했습니다: ' + (data.error || ''));
          }
      })
      .catch(error => {
          loadingIndicator.style.display = 'none';
          console.error('칸반보드 업데이트 오류:', error);
          alert('칸반보드 업데이트 중 오류가 발생했습니다: ' + error.message);
      });
}

// 칸반보드 새로고침 (현재 선택된 속성으로)
function refreshKanban() {
  const currentAttr = document.getElementById('kanbanAttributeSelect').value || window.SELECTED_KANBAN_ATTR;
  updateKanbanBoard(currentAttr);
}