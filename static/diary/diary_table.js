function openDropdown(td, type, id, currentId, currentSubregion) {
  closeDropdown();
  dropdown = document.createElement('div');
  dropdown.className = 'dropdown-edit';
  dropdown.style.top = (td.getBoundingClientRect().top + window.scrollY + td.offsetHeight) + 'px';
  dropdown.style.left = (td.getBoundingClientRect().left + window.scrollX) + 'px';
  
  if(type === 'region') {
      // 지역만 선택하는 드롭다운
      var regionNames = ['서울','경기','인천','대구','부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
      let selectedRegion = currentId || '서울';
      let html = '<div><b>지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
      regionNames.forEach(function(region) {
          html += '<li style="margin-bottom:2px;"><span data-region="'+region+'" style="cursor:pointer;'+(region==selectedRegion?'font-weight:bold;color:#007bff;':'')+'">'+region+'</span></li>';
      });
      html += '</ul></div>';
      dropdown.innerHTML = html;
      document.body.appendChild(dropdown);
      // 지역 클릭 시 바로 저장
      dropdown.querySelectorAll('span[data-region]').forEach(function(span) {
          span.onclick = function() {
              selectedRegion = this.getAttribute('data-region');
              td.innerText = selectedRegion;
              td.setAttribute('data-value', selectedRegion);
              // 상세지역 td도 같이 변경 (첫 번째 값으로 초기화)
              var subTd = td.parentElement.querySelector('td[data-field="subregion"]');
              if(subTd) {
                  var regionMap = {
                      '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
                      '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
                      '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
                      '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
                      '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
                      '광주': ['동구','서구','남구','북구','광산구'],
                      '대전': ['동구','중구','서구','유성구','대덕구'],
                      '울산': ['중구','남구','동구','북구','울주군'],
                      '세종': ['세종시'],
                      '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
                      '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
                      '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
                      '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
                      '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
                  };
                  var firstSubregion = (regionMap[selectedRegion] || [])[0] || '';
                  subTd.innerText = firstSubregion;
              }
              closeDropdown();
              fetch('/diary/update/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'id='+id+'&field=지역&value='+encodeURIComponent(selectedRegion)
              }).then(() => {
                  fetch('/diary/update/?id='+id)
                    .then(r=>r.json())
                    .then(function(data){
                        if(data.success && data.entry) {
                            updateTableRow(data.entry);
                            // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
                            if (window.kanbanAttribute && '지역' === window.kanbanAttribute) {
                                refreshKanban();
                            }
                            if (typeof window._modalAfterUpdateAll === 'function') window._modalAfterUpdateAll(id); window._modalAfterUpdateAll = null; 
                        }
                    });
              });
          };
      });
      document.addEventListener('mousedown', function handler(e) {
          if(dropdown && !dropdown.contains(e.target)) { closeDropdown(); document.removeEventListener('mousedown', handler); }
      });
      return;
  } else if(type === 'region_detail') {
      // 상세지역만 선택하는 드롭다운
      var regionMap = {
          '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
          '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
          '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
          '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
          '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
          '광주': ['동구','서구','남구','북구','광산구'],
          '대전': ['동구','중구','서구','유성구','대덕구'],
          '울산': ['중구','남구','동구','북구','울주군'],
          '세종': ['세종시'],
          '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
          '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
          '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
          '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
          '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
      };
      var currentRegion = td.parentElement.querySelector('td[data-field="지역"]').innerText.trim();
      var subregions = regionMap[currentRegion] || [];
      let selectedSubregion = currentSubregion || '';
      let html = '<div><b>상세지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
      subregions.forEach(function(sub) {
          html += '<li style="margin-bottom:2px;"><span data-subregion="'+sub+'" style="cursor:pointer;'+(sub==selectedSubregion?'font-weight:bold;color:#007bff;':'')+'">'+sub+'</span></li>';
      });
      html += '</ul></div>';
      dropdown.innerHTML = html;
      document.body.appendChild(dropdown);
      // 상세지역 클릭 시 바로 저장
      dropdown.querySelectorAll('span[data-subregion]').forEach(function(span) {
          span.onclick = function() {
              selectedSubregion = this.getAttribute('data-subregion');
              td.innerText = selectedSubregion;
              closeDropdown();
              // 서버에 상세지역 저장
              fetch('/diary/update/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'id='+id+'&field=상세지역&value='+encodeURIComponent(selectedSubregion)
              }).then(() => {
                  fetch('/diary/update/?id='+id)
                    .then(r=>r.json())
                    .then(function(data){
                        if(data.success && data.entry) {
                            updateTableRow(data.entry);
                            // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
                            if (window.kanbanAttribute && '상세지역' === window.kanbanAttribute) {
                                refreshKanban();
                            }
                            if (typeof window._modalAfterUpdateAll === 'function') { 
                                window._modalAfterUpdateAll(id); 
                                window._modalAfterUpdateAll = null; 
                            }
                        }
                    });
              });
          };
      });
  }
  
  // dropdown 타입인 경우 dropdown_options API 사용
  if(window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[type]) {
      const options = window.DROPDOWN_OPTIONS[type];
      let html = '<div><b>' + type + ' 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
      options.forEach(function(opt) {
          html += `<li style="display:flex;align-items:center;gap:6px;">
              <span data-option-id="${opt.id}" style="cursor:pointer;background:${opt.color ? hexToRgba(opt.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${opt.option}</span>
              <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
              <button data-edit="${opt.id}">✏️</button>
              <button data-del="${opt.id}">🗑️</button></li>`;
      });
      html += '</ul>';
      html += '<input type="text" placeholder="새 옵션 추가" style="width:70%;"> <button class="add-btn">추가</button></div>';
      dropdown.innerHTML = html;
      document.body.appendChild(dropdown);
      
      // 옵션 선택
      dropdown.querySelectorAll('span[data-option-id]').forEach(function(span){
          span.onclick = function(){
              const selectedOptionId = span.getAttribute('data-option-id');
              const selectedOptionText = span.innerText;
              const fieldName = td.getAttribute('data-field');
              const tr = td.closest('tr');
              const rowId = tr.getAttribute('data-id');
              
              // UI 업데이트
              td.innerText = selectedOptionText;
              td.setAttribute('data-value', selectedOptionId);
              td.style.background = span.style.background;
              closeDropdown();
              
              // 서버에 데이터 저장
              if (rowId && fieldName) {
                  fetch('/diary/update_row_field/', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                      body: 'id=' + encodeURIComponent(rowId) + '&field=' + encodeURIComponent(fieldName) + '&value=' + encodeURIComponent(selectedOptionId)
                  })
                  .then(r => r.json())
                  .then(function(data) {
                      if (data.success) {
                          // 성공 시 칸반보드 업데이트 (드롭다운 속성이 현재 칸반보드와 관련된 경우)
                          const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
                              document.getElementById('kanbanAttributeSelect').value : 
                              window.SELECTED_KANBAN_ATTR;
                          
                          // 변경된 필드가 현재 칸반보드에서 사용 중인 속성이면 칸반보드 새로고침
                          if (fieldName === currentKanbanAttr) {
                              console.log('칸반보드 속성이 변경되어 새로고침합니다:', fieldName);
                              refreshKanban();
                          }
                          
                          // F/U 일정 필드인 경우 캘린더도 새로고침
                          if (fieldName === 'F/U 일정' && window.calendar) {
                              window.calendar.refetchEvents();
                          }
                      } else {
                          alert('저장 실패: ' + (data.error || ''));
                          // 실패 시 UI 롤백
                          location.reload();
                      }
                  })
                  .catch(function(err) {
                      alert('저장 실패: 네트워크 오류');
                      console.error(err);
                      // 실패 시 UI 롤백
                      location.reload();
                  });
              }
          };
      });
      
      // 컬러피커
      dropdown.querySelectorAll('input[data-color-edit]').forEach(function(input){
          input.onchange = function(e){
              fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + input.getAttribute('data-color-edit') + '&color=' + encodeURIComponent(input.value), {
                  method: 'PUT'
              }).then(r => r.json()).then(data => {
                  if(data.success) {
                      // 색상 변경 즉시 반영
                      const span = input.closest('li').querySelector('span[data-option-id]');
                      span.style.background = hexToRgba(input.value, 0.18);
                      
                      // 전역 DROPDOWN_OPTIONS도 업데이트
                      if(window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[type]) {
                          const option = window.DROPDOWN_OPTIONS[type].find(opt => opt.id == input.getAttribute('data-color-edit'));
                          if(option) option.color = input.value;
                      }
                  }
              }).catch(error => {
                  console.error('색상 변경 실패:', error);
              });
          };
      });
      
      // 추가
      dropdown.querySelector('.add-btn').onclick = function(){
          const val = dropdown.querySelector('input[type=text]').value.trim();
          if(val) {
              fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type), {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'name=' + encodeURIComponent(val)
              })
              .then(r => r.json())
              .then(data => {
                  if(data.id && data.option) {
                      // 새로 추가된 옵션을 드롭다운에 동적으로 추가
                      const ul = dropdown.querySelector('ul');
                      const li = document.createElement('li');
                      li.style.cssText = 'display:flex;align-items:center;gap:6px;';
                      li.innerHTML = `
                          <span data-option-id="${data.id}" style="cursor:pointer;background:${data.color ? hexToRgba(data.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${data.option}</span>
                          <input type="color" value="${data.color||'#eeeeee'}" data-color-edit="${data.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
                          <button data-edit="${data.id}">✏️</button>
                          <button data-del="${data.id}">🗑️</button>
                      `;
                      ul.appendChild(li);
                      
                      // 새로 추가된 옵션에 이벤트 바인딩
                      const span = li.querySelector('span[data-option-id]');
                      span.onclick = function(){
                          td.innerText = span.innerText;
                          td.setAttribute('data-value', span.getAttribute('data-option-id'));
                          td.style.background = span.style.background;
                          closeDropdown();
                          fetch('/diary/update/', {
                              method: 'POST',
                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                              body: 'id='+id+'&field='+type+'&value='+encodeURIComponent(span.getAttribute('data-option-id'))
                          }).then(() => {
                              fetch('/diary/update/?id='+id)
                                .then(r=>r.json())
                                .then(function(data){
                                    if(data.success && data.entry) {
                                        updateTableRow(data.entry);
                                        refreshKanban();
                                        if (typeof window._modalAfterUpdateAll === 'function') { 
                                            window._modalAfterUpdateAll(id); 
                                            window._modalAfterUpdateAll = null; 
                                        }
                                    }
                                });
                          });
                      };
                      
                      // 컬러피커 이벤트
                      const colorInput = li.querySelector('input[data-color-edit]');
                      colorInput.onchange = function(e){
                          fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + colorInput.getAttribute('data-color-edit') + '&color=' + encodeURIComponent(colorInput.value), {
                              method: 'PUT'
                          }).then(r => r.json()).then(data => {
                              if(data.success) {
                                  // 색상 변경 즉시 반영
                                  span.style.background = hexToRgba(colorInput.value, 0.18);
                              }
                          });
                      };
                      
                      // 삭제 버튼 이벤트
                      const delBtn = li.querySelector('button[data-del]');
                      delBtn.onclick = function(e){
                          e.stopPropagation();
                          if(confirm('삭제할까요?')) {
                              fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + delBtn.getAttribute('data-del'), {
                                  method: 'DELETE'
                              }).then(r => r.json()).then(data => {
                                  if(data.success) {
                                      li.remove();
                                  }
                              });
                          }
                      };
                      
                      // 수정 버튼 이벤트
                      const editBtn = li.querySelector('button[data-edit]');
                      editBtn.onclick = function(e){
                          e.stopPropagation();
                          const li = btn.closest('li');
                          const span = li.querySelector('span[data-option-id]');
                          const old = span.innerText;
                          const input = document.createElement('input');
                          input.type = 'text'; input.value = old;
                          input.className = 'table-edit-input';
                          span.replaceWith(input);
                          input.focus();
                          input.onkeydown = function(ev){
                              if(ev.key==='Enter'){
                                  fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + editBtn.getAttribute('data-edit') + '&name=' + encodeURIComponent(input.value), {
                                      method: 'PUT'
                                  }).then(r => r.json()).then(data => {
                                      if(data.success) {
                                          const newSpan = document.createElement('span');
                                          newSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                                          newSpan.style.cssText = span.style.cssText;
                                          newSpan.innerText = input.value;
                                          newSpan.onclick = span.onclick;
                                          input.replaceWith(newSpan);
                                          span = newSpan; // 참조 업데이트
                                      }
                                  }).catch(error => {
                                      console.error('수정 실패:', error);
                                      // 실패시 원래 값으로 복원
                                      const restoredSpan = document.createElement('span');
                                      restoredSpan.setAttribute('data-option-id', btn.getAttribute('data-edit'));
                                      restoredSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                                      restoredSpan.innerText = old;
                                      input.replaceWith(restoredSpan);
                                  });
                              } else if(ev.key==='Escape') {
                                  // ESC 키로 취소
                                  const cancelSpan = document.createElement('span');
                                  cancelSpan.setAttribute('data-option-id', btn.getAttribute('data-edit'));
                                  cancelSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                                  cancelSpan.innerText = old;
                                  input.replaceWith(cancelSpan);
                              }
                          };
                      };
                      
                      // 입력 필드 초기화
                      dropdown.querySelector('input[type=text]').value = '';
                      
                      // 전역 DROPDOWN_OPTIONS도 업데이트
                      if(window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[type]) {
                          window.DROPDOWN_OPTIONS[type].push({
                              id: data.id,
                              option: data.option,
                              color: data.color
                          });
                      }
                  }
              })
              .catch(error => {
                  console.error('옵션 추가 실패:', error);
                  alert('옵션 추가에 실패했습니다.');
              });
          }
      };
      
      // 삭제
      dropdown.querySelectorAll('button[data-del]').forEach(function(btn){
          btn.onclick = function(e){
              e.stopPropagation();
              if(confirm('삭제할까요?')) {
                  fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + btn.getAttribute('data-del'), {
                      method: 'DELETE'
                  }).then(r => r.json()).then(data => {
                      if(data.success) {
                          // 해당 li 요소 제거
                          btn.closest('li').remove();
                          
                          // 전역 DROPDOWN_OPTIONS에서도 제거
                          if(window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[type]) {
                              const delId = btn.getAttribute('data-del');
                              window.DROPDOWN_OPTIONS[type] = window.DROPDOWN_OPTIONS[type].filter(opt => opt.id != delId);
                          }
                      }
                  }).catch(error => {
                      console.error('삭제 실패:', error);
                      alert('삭제에 실패했습니다.');
                  });
              }
          };
      });
      
      // 수정
      dropdown.querySelectorAll('button[data-edit]').forEach(function(btn){
          btn.onclick = function(e){
              e.stopPropagation();
              const li = btn.closest('li');
              const span = li.querySelector('span[data-option-id]');
              const old = span.innerText;
              const input = document.createElement('input');
              input.type = 'text'; input.value = old;
              input.className = 'table-edit-input';
              span.replaceWith(input);
              input.focus();
              input.onkeydown = function(ev){
                  if(ev.key==='Enter'){
                      fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + btn.getAttribute('data-edit') + '&name=' + encodeURIComponent(input.value), {
                          method: 'PUT'
                      }).then(r => r.json()).then(data => {
                          if(data.success) {
                              // 수정된 내용 즉시 반영
                              const newSpan = document.createElement('span');
                              newSpan.setAttribute('data-option-id', btn.getAttribute('data-edit'));
                              newSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                              newSpan.innerText = input.value;
                              
                              // 클릭 이벤트 재바인딩
                              newSpan.onclick = function(){
                                  td.innerText = newSpan.innerText;
                                  td.setAttribute('data-value', newSpan.getAttribute('data-option-id'));
                                  td.style.background = newSpan.style.background;
                                  closeDropdown();
                                  fetch('/diary/update/', {
                                      method: 'POST',
                                      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                      body: 'id='+id+'&field='+type+'&value='+encodeURIComponent(newSpan.getAttribute('data-option-id'))
                                  }).then(() => {
                                      fetch('/diary/update/?id='+id)
                                        .then(r=>r.json())
                                        .then(function(data){
                                            if(data.success && data.entry) {
                                                updateTableRow(data.entry);
                                                refreshKanban();
                                                if (typeof window._modalAfterUpdateAll === 'function') { 
                                                    window._modalAfterUpdateAll(id); 
                                                    window._modalAfterUpdateAll = null; 
                                                }
                                            }
                                        });
                                  });
                              };
                              
                              input.replaceWith(newSpan);
                              
                              // 전역 DROPDOWN_OPTIONS도 업데이트
                              if(window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[type]) {
                                  const option = window.DROPDOWN_OPTIONS[type].find(opt => opt.id == btn.getAttribute('data-edit'));
                                  if(option) option.option = input.value;
                              }
                          }
                      }).catch(error => {
                          console.error('수정 실패:', error);
                          // 실패시 원래 값으로 복원
                          const restoredSpan = document.createElement('span');
                          restoredSpan.setAttribute('data-option-id', btn.getAttribute('data-edit'));
                          restoredSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                          restoredSpan.innerText = old;
                          input.replaceWith(restoredSpan);
                      });
                  } else if(ev.key==='Escape') {
                      // ESC 키로 취소
                      const cancelSpan = document.createElement('span');
                      cancelSpan.setAttribute('data-option-id', btn.getAttribute('data-edit'));
                      cancelSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                      cancelSpan.innerText = old;
                      input.replaceWith(cancelSpan);
                  }
              };
          };
      });
      
      document.addEventListener('mousedown', function handler(e) {
          if(dropdown && !dropdown.contains(e.target)) { closeDropdown(); document.removeEventListener('mousedown', handler); }
      });
  }
}

function bindTableCellEvents() {
    document.querySelectorAll('td[data-field]').forEach(function(td) {
        const type = td.getAttribute('data-field');
        const dataType = td.getAttribute('data-type');
        if (dataType === 'datetime') {
            const input = td.querySelector('input[type="date"]');
            if (input) {
                input.onchange = function() {
                    const id = td.parentElement.getAttribute('data-id');
                    const newValue = input.value;
                    fetch('/diary/update/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id=' + id + '&field=' + type + '&value=' + encodeURIComponent(newValue)
                    }).then(function(response) {
                        return response.json();
                    }).then(function(data) {
                        if (!data.success) alert('수정 실패: ' + data.error);
                        // 필요시 테이블/보드 갱신
                    });
                };
            } else {
                // input이 없는 경우 클릭 시 생성
                td.onclick = function() {
                    if (td.querySelector('input')) return;
                    td.style.width = td.offsetWidth + 'px';
                    
                    const oldValue = td.innerText.trim();
                    const id = td.parentElement.getAttribute('data-id');
                    
                    const input = document.createElement('input');
                    input.type = 'date';
                    input.value = oldValue ? oldValue.slice(0,10) : '';
                    input.className = 'table-edit-input';
                    input.style.position = 'absolute';
                    input.style.left = '0';
                    input.style.top = '0';
                    input.style.width = 'max-content';
                    input.style.minWidth = '100%';
                    input.style.background = '#fffbe6';
                    input.style.zIndex = '10';
                    input.style.border = 'none';
                    input.style.fontSize = 'inherit';
                    input.style.fontFamily = 'inherit';
                    input.style.lineHeight = 'inherit';
                    input.style.padding = '0';
                    input.style.margin = '0';
                    
                    td.appendChild(input);
                    input.focus();
                    
                    input.onblur = function() {
                        const newValue = input.value;
                        td.innerText = newValue;
                        td.style.width = '';
                        
                        // 서버에 업데이트
                        fetch('/diary/update/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                        }).then(function(response) {
                            return response.json();
                        }).then(function(data) {
                            if (!data.success) alert('수정 실패: ' + (data.error || ''));
                        }).catch(function(error) {
                            console.error('업데이트 중 오류:', error);
                        });
                    };
                    
                    input.onkeydown = function(e) {
                        if (e.key === 'Enter') input.blur();
                        if (e.key === 'Escape') { 
                            td.innerText = oldValue;
                            td.style.width = '';
                        }
                    };
                };
            }
        } else if(dataType === 'dropdown' || dataType === 'region' || dataType === 'region_detail') {
            td.onclick = function(e) {
                const id = td.parentElement.getAttribute('data-id');
                if(dataType === 'region') {
                    // 이름 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                    const currentValue = (type === '이름') ? 
                        (td.querySelector('.name-text')?.innerText.trim() || '') : 
                        td.innerText.trim();
                    const regionValue = td.parentElement.querySelector('td[data-field="지역"]');
                    const regionText = regionValue ? 
                        (regionValue.getAttribute('data-field') === '이름' ? 
                            (regionValue.querySelector('.name-text')?.innerText.trim() || '') : 
                            regionValue.innerText.trim()) : '';
                    openDropdown(td, 'region', id, currentValue, regionText);
                } else if(dataType === 'region_detail') {
                    const regionTd = td.parentElement.querySelector('td[data-field="지역"]');
                    const regionValue = regionTd ? 
                        (regionTd.getAttribute('data-field') === '이름' ? 
                            (regionTd.querySelector('.name-text')?.innerText.trim() || '') : 
                            regionTd.innerText.trim()) : '';
                    const currentValue = (type === '이름') ? 
                        (td.querySelector('.name-text')?.innerText.trim() || '') : 
                        td.innerText.trim();
                    openDropdown(td, 'region_detail', id, regionValue, currentValue);
                } else if(dataType === 'dropdown') {
                    openDropdown(td, type, id, td.getAttribute('data-value'));
                }
            };
        } else {
            td.onclick = function() {
                if (td.querySelector('input')) return;
                td.style.width = td.offsetWidth + 'px';
                if(type === '이름') {
                    const nameDiv = td.querySelector('.name-text');
                    if(!nameDiv) return;
                    const oldValue = nameDiv.innerText;
                    const id = td.parentElement.getAttribute('data-id');
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = oldValue;
                    input.className = 'table-edit-input';
                    nameDiv.innerHTML = '';
                    nameDiv.appendChild(input);
                    // ...버튼 숨김
                    const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                    if(moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                    input.focus();
                    function restoreCell(value) {
                        td.innerHTML = `<div class="name-text">${value}</div><div class="more-btn-wrapper"><div class="more-btn" style="cursor:pointer;">⋯</div></div>`;
                        // ...버튼 이벤트 재바인딩
                        const newMoreBtn = td.querySelector('.more-btn');
                        if(newMoreBtn) {
                            newMoreBtn.onclick = function(e){
                                e.stopPropagation();
                                const tr = td.closest('tr');
                                const id = tr.getAttribute('data-id');
                                if(!id) { alert('ID 정보가 없습니다.'); return; }
                                // 새로운 Row 시스템의 get_row_details 엔드포인트 사용
                                fetch('/diary/get_row_details/'+id+'/')
                                  .then(r => r.json())
                                  .then(function(data){
                                      if(data.success) showDetailModal(data.row_data, data.row_id);
                                      else alert('상세정보 불러오기 실패: '+(data.error||''));
                                  })
                                  .catch(function(err){
                                      alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                      console.error(err);
                                  });
                            };
                        }
                        // 편집 종료 시 td width 해제
                        td.style.width = '';
                    }
                    input.onblur = function() {
                        const newValue = input.value;
                        restoreCell(newValue);
                        fetch('/diary/update/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            body: 'id='+id+'&field=이름&value='+encodeURIComponent(newValue)
                        });
                    };
                    input.onkeydown = function(e) {
                        if (e.key === 'Enter') input.blur();
                        if (e.key === 'Escape') restoreCell(oldValue);
                    };
                } else {
                    // 일반 텍스트 필드들 처리
                    // 이름 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                    const oldValue = (type === '이름') ? 
                        (td.querySelector('.name-text')?.innerText || '') : 
                        td.innerText;
                    const id = td.parentElement.getAttribute('data-id');
                    
                    let inputType = 'text';
                    // 날짜 필드들은 date input 사용
                    if (['TA','미팅','F/U 일정'].includes(type) || dataType === 'datetime') {
                        inputType = 'date';
                    }
                    
                    const input = document.createElement('input');
                    input.type = inputType;
                    input.value = (inputType==='date' && oldValue) ? oldValue.trim().slice(0,10) : oldValue.trim();
                    input.className = 'table-edit-input';
                    input.style.position = 'absolute';
                    input.style.left = '0';
                    input.style.top = '0';
                    input.style.width = 'max-content';
                    input.style.minWidth = '100%';
                    input.style.background = '#fffbe6';
                    input.style.zIndex = '10';
                    input.style.border = 'none';
                    input.style.fontSize = 'inherit';
                    input.style.fontFamily = 'inherit';
                    input.style.lineHeight = 'inherit';
                    input.style.padding = '0';
                    input.style.margin = '0';
                    
                    td.appendChild(input);
                    input.focus();
                    if(inputType === 'text') input.select();
                    
                    input.onblur = function() {
                        const newValue = input.value;
                        // 이름 필드인 경우 .name-text 업데이트, 다른 필드는 td.innerText 업데이트
                        if(type === '이름') {
                            const nameTextDiv = td.querySelector('.name-text');
                            if(nameTextDiv) nameTextDiv.innerText = newValue;
                            if(input.parentNode) input.parentNode.removeChild(input);
                        } else {
                            td.innerText = newValue;
                        }
                        // 편집 종료 시 td width 해제
                        td.style.width = '';
                        
                        // 서버에 업데이트
                        fetch('/diary/update/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                        }).then(function(response) {
                            return response.json();
                        }).then(function(data) {
                            if (!data.success) alert('수정 실패: ' + (data.error || ''));
                        }).catch(function(error) {
                            console.error('업데이트 중 오류:', error);
                        });
                    };
                    
                    input.onkeydown = function(e) {
                        if (e.key === 'Enter') input.blur();
                        if (e.key === 'Escape') { 
                            // 이름 필드인 경우 .name-text 복원, 다른 필드는 td.innerText 복원
                            if(type === '이름') {
                                const nameTextDiv = td.querySelector('.name-text');
                                if(nameTextDiv) nameTextDiv.innerText = oldValue;
                                if(input.parentNode) input.parentNode.removeChild(input);
                            } else {
                                td.innerText = oldValue;
                            }
                            td.style.width = '';
                        }
                    };
                }
            };
        }
    });
}

function refreshTable() {
    fetch('/').then(r=>r.text()).then(html=>{
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newTable = temp.querySelector('#entryTable');
        if (newTable) {
            document.getElementById('entryTable').innerHTML = newTable.innerHTML;
            bindTableCellEvents(); // 테이블 이벤트 복구
            
            // 정렬/필터 데이터 재초기화
            initializeTableData();
            
            // 현재 필터 상태 재적용
            if (Object.keys(window.filters).length > 0) {
                Object.entries(window.filters).forEach(([column, filterValue]) => {
                    // 필터 입력창에 값 복원
                    const filterInput = document.querySelector(`input[data-column="${column}"]`);
                    if (filterInput) {
                        filterInput.value = filterValue;
                    }
                    
                    // 필터 재적용
                    window.originalRows.forEach(row => {
                        let shouldShow = true;
                        
                        for (const [filterColumn, filterVal] of Object.entries(window.filters)) {
                            const cellValue = getCellValue(row, filterColumn).toLowerCase();
                            if (!cellValue.includes(filterVal)) {
                                shouldShow = false;
                                break;
                            }
                        }
                        
                        row.style.display = shouldShow ? '' : 'none';
                    });
                });
            }
            
            // 현재 정렬 상태 재적용
            if (window.currentSort.column) {
                sortTable(window.currentSort.column, window.currentSort.direction);
            }
            
            updateFilterStatus();
        }
    });
}


// 새로운 필드 업데이트 함수
function updateRowField(rowId, field, value) {
    fetch('/diary/update_row_field/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'id='+encodeURIComponent(rowId)+'&field='+encodeURIComponent(field)+'&value='+encodeURIComponent(value)
    })
    .then(r=>r.json())
    .then(function(data){
        if(!data.success) {
            alert('수정 실패: '+(data.error||''));
            return;
        }
        // 성공 시 테이블과 칸반보드 새로고침
        refreshTable();
        // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
        if (window.kanbanAttribute && field === window.kanbanAttribute) {
            refreshKanban();
        }
        // F/U 일정 필드인 경우 캘린더도 새로고침
        if(field === 'F/U 일정' && window.calendar) {
            window.calendar.refetchEvents();
        }
        // 모달 데이터도 새로고침
        fetch('/diary/get_row_details/'+rowId+'/')
          .then(r => r.json())
          .then(function(data){
              if(data.success) showDetailModal(data.row_data, data.row_id);
          });
    })
    .catch(function(err){
        alert('수정 실패: 네트워크 오류');
        console.error(err);
    });
}


// 새 행용 Attribute 시스템 이벤트 바인딩
function bindNewRowAttributeEvents(tr) {
    tr.querySelectorAll('td[data-field]').forEach(function(td) {
        const field = td.getAttribute('data-field');
        const type = td.getAttribute('data-type');
        
        console.log(`새 행 필드 "${field}" 이벤트 바인딩, type: ${type}`);
        
        // datetime 타입 필드들
        if (type === 'datetime') {
            const input = td.querySelector('input[type="date"]');
            if (input) {
                input.onchange = function() {
                    const newValue = input.value;
                    console.log(`새 행 datetime 필드 "${field}" 값 변경:`, newValue);
                    // 새 행 필드 저장
                    saveNewRowField(tr, field, newValue);
                };
            }
        }
        // dropdown 타입이나 특수 지역 필드들
        else if(type === 'dropdown' || field === '지역' || field === '상세지역') {
            td.style.cursor = 'pointer';
            td.onclick = function(e) {
                console.log(`새 행 드롭다운 클릭됨 - 필드: ${field}, type: ${type}`);
                e.stopPropagation();
                
                let dropdownType = '';
                if(type === 'dropdown') {
                    // 필드명을 그대로 사용 (영어 매핑 제거)
                    dropdownType = field;
                    console.log(`dropdown 타입: ${field}`);
                } else if(field === '지역') {
                    dropdownType = 'region';
                    console.log('지역 드롭다운으로 설정');
                } else if(field === '상세지역') {
                    dropdownType = 'region_detail';
                    console.log('상세지역 드롭다운으로 설정');
                }
                
                if(dropdownType) {
                    // 이름 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                    const currentValue = (field === '이름') ? 
                        (td.querySelector('.name-text')?.innerText || '') : 
                        (td.innerText || '');
                    const currentSubregion = dropdownType === 'region_detail' ? 
                        tr.querySelector('td[data-field="상세지역"]').innerText : '';
                    
                    // 새 행용 드롭다운 열기
                    openNewRowAttributeDropdown(td, dropdownType, currentValue, currentSubregion, tr);
                }
            };
        }
        // 이름 필드 특별 처리
        else if(field === '이름') {
            td.onclick = function(e) {
                e.stopPropagation();
                if(e.target.classList.contains('more-btn')) return;
                
                const nameTextDiv = td.querySelector('.name-text');
                const oldValue = nameTextDiv.innerText;
                
                const input = document.createElement('input');
                input.type = 'text';
                input.value = oldValue;
                input.className = 'table-edit-input';
                input.style.position = 'absolute';
                input.style.left = '0';
                input.style.top = '0';
                input.style.width = 'max-content';
                input.style.minWidth = '100%';
                input.style.background = '#fffbe6';
                input.style.zIndex = '10';
                input.style.border = 'none';
                input.style.fontSize = 'inherit';
                input.style.fontFamily = 'inherit';
                input.style.lineHeight = 'inherit';
                input.style.padding = '0';
                input.style.margin = '0';
                
                td.appendChild(input);
                input.focus();
                input.select();
                
                function restoreCell(newValue) {
                    nameTextDiv.innerText = newValue;
                    if(input.parentNode) input.parentNode.removeChild(input);
                }
                
                input.onblur = function() {
                    const newValue = input.value;
                    restoreCell(newValue);
                    console.log(`새 행 이름 필드 값 변경:`, newValue);
                    // 새 행 필드 저장
                    saveNewRowField(tr, field, newValue);
                };
                
                input.onkeydown = function(e) {
                    if (e.key === 'Enter') input.blur();
                    if (e.key === 'Escape') restoreCell(oldValue);
                };
            };
        }
        // 일반 텍스트 필드들
        else {
            td.onclick = function(e) {
                e.stopPropagation();
                const oldValue = td.innerText;
                
                let inputType = 'text';
                // 날짜 필드들은 date input 사용
                if (['TA','미팅','F/U 일정'].includes(field) || type === 'datetime') {
                    inputType = 'date';
                }
                
                const input = document.createElement('input');
                input.type = inputType;
                input.value = (inputType==='date' && oldValue) ? oldValue.trim().slice(0,10) : oldValue.trim();
                input.className = 'table-edit-input';
                
                td.innerHTML = '';
                td.appendChild(input);
                input.focus();
                if(inputType === 'text') input.select();
                
                input.onblur = function() {
                    const newValue = input.value;
                    td.innerText = newValue;
                    console.log(`새 행 일반 필드 "${field}" 값 변경:`, newValue);
                    // 새 행 필드 저장
                    saveNewRowField(tr, field, newValue);
                };
                
                input.onkeydown = function(e) {
                    if (e.key === 'Enter') input.blur();
                    if (e.key === 'Escape') { td.innerText = oldValue; }
                };
            };
        }
    });
}

// 새 행 필드 값 저장 함수 (수정됨)
function saveNewRowField(tr, field, value) {
    const currentId = tr.getAttribute('data-id');
    console.log(`새 행 필드 저장: ${field} = ${value}, 현재 ID: ${currentId}`);
    
    // 임시 ID인 경우 (새 행 생성)
    if (currentId && currentId.startsWith('temp_')) {
        console.log('새 행 생성 중...');
        fetch('/diary/create_new_row/', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(value)
        }).then(function(response) {
            console.log(`새 행 생성 응답 상태:`, response.status);
            return response.json();
        }).then(function(data) {
            console.log(`새 행 생성 응답:`, data);
            if (data.success && data.id) {
                // 임시 ID를 실제 ID로 변경
                tr.setAttribute('data-id', data.id);
                tr.removeAttribute('data-is-new');
                console.log(`새 행 ID 업데이트: ${currentId} -> ${data.id}`);
                
                // 현재 칸반보드에서 사용 중인 속성이 변경된 경우 칸반보드 새로고침
                const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
                    document.getElementById('kanbanAttributeSelect').value : 
                    window.SELECTED_KANBAN_ATTR;
                
                if (field === currentKanbanAttr) {
                    console.log('새 행 생성 시 칸반보드 속성이 변경되어 새로고침합니다:', field);
                    refreshKanban();
                }
                
                // F/U 일정 필드인 경우 캘린더 새로고침
                if (field === 'F/U 일정' && window.calendar) {
                    window.calendar.refetchEvents();
                }
            }
        }).catch(function(error) {
            console.error(`새 행 생성 중 오류:`, error);
            alert('새 행 생성 중 오류 발생: ' + error.message);
        });
    }
    // 실제 ID가 있는 경우 (기존 행 업데이트)
    else if (currentId && !currentId.startsWith('temp_')) {
        console.log('기존 행 업데이트 중...');
        fetch('/diary/update_row_field/', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'id=' + encodeURIComponent(currentId) + '&field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(value)
        }).then(function(response) {
            console.log(`${field} 필드 업데이트 응답 상태:`, response.status);
            return response.json();
        }).then(function(data) {
            console.log(`${field} 필드 업데이트 응답:`, data);
            if (data.success) {
                // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우 새로고침
                if (window.kanbanAttribute && field === window.kanbanAttribute) {
                    refreshKanban();
                }
                // F/U 일정 필드인 경우 캘린더 새로고침
                if (field === 'F/U 일정' && window.calendar) {
                    window.calendar.refetchEvents();
                }
            } else {
                console.error(`${field} 필드 업데이트 실패:`, data.error);
                alert('업데이트 실패: ' + (data.error || ''));
            }
        }).catch(function(error) {
            console.error(`${field} 필드 업데이트 중 오류:`, error);
            alert('업데이트 중 오류 발생: ' + error.message);
        });
    } else {
        console.error('유효하지 않은 행 ID:', currentId);
    }
}

// 새 행용 드롭다운 함수 (Attribute 시스템)
function openNewRowAttributeDropdown(td, type, currentValue, currentSubregion, tr) {
    console.log('새 행 attribute 드롭다운 호출됨');
    console.log('파라미터:', {type, currentValue, currentSubregion});
    
    closeDropdown();
    dropdown = document.createElement('div');
    dropdown.className = 'dropdown-edit';
    dropdown.style.top = (td.getBoundingClientRect().top + window.scrollY + td.offsetHeight) + 'px';
    dropdown.style.left = (td.getBoundingClientRect().left + window.scrollX) + 'px';
    
    if(type === 'region') {
        // 지역 드롭다운 (하드코딩된 값들)
        var regionNames = ['서울','경기','인천','대구','부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
        let selectedRegion = currentValue || '서울';
        let html = '<div><b>지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
        regionNames.forEach(function(region) {
            html += '<li style="margin-bottom:2px;"><span data-region="'+region+'" style="cursor:pointer;'+(region==selectedRegion?'font-weight:bold;color:#007bff;':'')+'">'+region+'</span></li>';
        });
        html += '</ul></div>';
        dropdown.innerHTML = html;
        document.body.appendChild(dropdown);
        
        dropdown.querySelectorAll('span[data-region]').forEach(function(span) {
            span.onclick = function() {
                selectedRegion = this.getAttribute('data-region');
                td.innerText = selectedRegion;
                td.setAttribute('data-value', selectedRegion);
                // 상세지역도 업데이트
                var subTd = tr.querySelector('td[data-field="상세지역"]');
                if(subTd) {
                    var regionMap = {
                        '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
                        '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군']
                    };
                    var firstSubregion = (regionMap[selectedRegion] || [])[0] || '';
                    subTd.innerText = firstSubregion;
                }
                closeDropdown();
                // 지역 값 저장
                saveNewRowField(tr, '지역', selectedRegion);
            };
        });
    } else if(type === 'region_detail') {
        // 상세지역 드롭다운 (하드코딩된 값들)
        var regionMap = {
            '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
            '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군']
        };
        var currentRegion = tr.querySelector('td[data-field="지역"]').innerText.trim();
        var subregions = regionMap[currentRegion] || [];
        let selectedSubregion = currentSubregion || '';
        let html = '<div><b>상세지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
        subregions.forEach(function(sub) {
            html += '<li style="margin-bottom:2px;"><span data-subregion="'+sub+'" style="cursor:pointer;'+(sub==selectedSubregion?'font-weight:bold;color:#007bff;':'')+'">'+sub+'</span></li>';
        });
        html += '</ul></div>';
        dropdown.innerHTML = html;
        document.body.appendChild(dropdown);
        
        dropdown.querySelectorAll('span[data-subregion]').forEach(function(span) {
            span.onclick = function() {
                selectedSubregion = this.getAttribute('data-subregion');
                td.innerText = selectedSubregion;
                closeDropdown();
                // 상세지역 값 저장
                saveNewRowField(tr, '상세지역', selectedSubregion);
            };
        });
    } else {
        // dropdown_options API를 사용하는 드롭다운 (구분, 영업진행, 가능성 등)
        fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type))
            .then(r => r.json())
            .then(function(data) {
                if (data.options) {
                    const options = data.options;
                    let html = '<div><b>' + type + ' 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
                    options.forEach(function(opt) {
                        html += `<li style="display:flex;align-items:center;gap:6px;">
                            <span data-option-id="${opt.id}" style="cursor:pointer;background:${opt.color ? hexToRgba(opt.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${opt.option}</span>
                            <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
                            <button data-edit="${opt.id}">✏️</button>
                            <button data-del="${opt.id}">🗑️</button>
                        </li>`;
                    });
                    html += '</ul>';
                    html += '<input type="text" placeholder="새 옵션 추가" style="width:70%;"> <button class="add-btn">추가</button></div>';
                    dropdown.innerHTML = html;
                    document.body.appendChild(dropdown);
                    
                    // 옵션 선택
                    dropdown.querySelectorAll('span[data-option-id]').forEach(function(span){
                        span.onclick = function(){
                            td.innerText = span.innerText;
                            td.setAttribute('data-value', span.getAttribute('data-option-id'));
                            td.style.background = span.style.background;
                            closeDropdown();
                            // 드롭다운 값 저장
                            saveNewRowField(tr, type, span.getAttribute('data-option-id'));
                        };
                    });
                    
                    // 새 항목 추가
                    dropdown.querySelector('.add-btn').onclick = function(){
                        const val = dropdown.querySelector('input[type=text]').value.trim();
                        if(val) {
                            fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type), {
                                method: 'POST',
                                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                body: 'name=' + encodeURIComponent(val)
                            })
                            .then(r => r.json())
                            .then(data => {
                                if(data.id && data.option) {
                                    // 새로 추가된 옵션을 드롭다운에 동적으로 추가
                                    const ul = dropdown.querySelector('ul');
                                    const li = document.createElement('li');
                                    li.style.cssText = 'display:flex;align-items:center;gap:6px;';
                                    li.innerHTML = `
                                        <span data-option-id="${data.id}" style="cursor:pointer;background:${data.color ? hexToRgba(data.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${data.option}</span>
                                        <input type="color" value="${data.color||'#eeeeee'}" data-color-edit="${data.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
                                        <button data-edit="${data.id}">✏️</button>
                                        <button data-del="${data.id}">🗑️</button>
                                    `;
                                    ul.appendChild(li);
                                    
                                    // 새로 추가된 옵션에 이벤트 바인딩
                                    const span = li.querySelector('span[data-option-id]');
                                    span.onclick = function(){
                                        td.innerText = span.innerText;
                                        td.setAttribute('data-value', span.getAttribute('data-option-id'));
                                        td.style.background = span.style.background;
                                        closeDropdown();
                                        // 드롭다운 값 저장
                                        saveNewRowField(tr, type, span.getAttribute('data-option-id'));
                                    };
                                    
                                    // 새 옵션의 컬러피커, 삭제, 수정 버튼 이벤트 바인딩
                                    bindNewRowDropdownItemEvents(li, type, tr);
                                    
                                    // 입력 필드 초기화
                                    dropdown.querySelector('input[type=text]').value = '';
                                }
                            })
                            .catch(error => {
                                console.error('옵션 추가 실패:', error);
                                alert('옵션 추가에 실패했습니다.');
                            });
                        }
                    };
                    
                    // 기존 옵션들에 이벤트 바인딩
                    dropdown.querySelectorAll('li').forEach(function(li) {
                        bindNewRowDropdownItemEvents(li, type, tr);
                    });
                }
            })
            .catch(function(error) {
                console.error('드롭다운 옵션 로드 실패:', error);
            });
    }
    
    // 외부 클릭 시 드롭다운 닫기
    document.addEventListener('mousedown', function(e) {
        if(dropdown && !dropdown.contains(e.target)) { 
            closeDropdown(); 
            document.removeEventListener('mousedown', handler); 
        }
    });
}

// 새 행 드롭다운 항목에 이벤트 바인딩하는 함수
function bindNewRowDropdownItemEvents(li, type, tr) {
    // 컬러피커 이벤트
    const colorInput = li.querySelector('input[data-color-edit]');
    if(colorInput) {
        colorInput.onchange = function(e){
            fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + colorInput.getAttribute('data-color-edit') + '&color=' + encodeURIComponent(colorInput.value), {
                method: 'PUT'
            }).then(r => r.json()).then(data => {
                if(data.success) {
                    // 색상 변경 즉시 반영
                    const span = li.querySelector('span[data-option-id]');
                    span.style.background = hexToRgba(colorInput.value, 0.18);
                }
            }).catch(error => {
                console.error('색상 변경 실패:', error);
            });
        };
    }
    
    // 삭제 버튼 이벤트
    const delBtn = li.querySelector('button[data-del]');
    if(delBtn) {
        delBtn.onclick = function(e){
            e.stopPropagation();
            if(confirm('삭제할까요?')) {
                fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + delBtn.getAttribute('data-del'), {
                    method: 'DELETE'
                }).then(r => r.json()).then(data => {
                    if(data.success) {
                        li.remove();
                    }
                }).catch(error => {
                    console.error('삭제 실패:', error);
                    alert('삭제에 실패했습니다.');
                });
            }
        };
    }
    
    // 수정 버튼 이벤트
    const editBtn = li.querySelector('button[data-edit]');
    if(editBtn) {
        editBtn.onclick = function(e){
            e.stopPropagation();
            const span = li.querySelector('span[data-option-id]');
            const old = span.innerText;
            const input = document.createElement('input');
            input.type = 'text'; input.value = old;
            input.className = 'table-edit-input';
            span.replaceWith(input);
            input.focus();
            input.onkeydown = function(ev){
                if(ev.key==='Enter'){
                    fetch('/diary/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + editBtn.getAttribute('data-edit') + '&name=' + encodeURIComponent(input.value), {
                        method: 'PUT'
                    }).then(r => r.json()).then(data => {
                        if(data.success) {
                            // 수정된 내용 즉시 반영
                            const newSpan = document.createElement('span');
                            newSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                            newSpan.style.cssText = 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                            newSpan.innerText = input.value;
                            
                            // 클릭 이벤트 재바인딩
                            newSpan.onclick = function(){
                                const td = tr.querySelector('td[data-field="' + type + '"]');
                                if(td) {
                                    td.innerText = newSpan.innerText;
                                    td.setAttribute('data-value', newSpan.getAttribute('data-option-id'));
                                    td.style.background = newSpan.style.background;
                                    closeDropdown();
                                    // 드롭다운 값 저장
                                    saveNewRowField(tr, type, newSpan.getAttribute('data-option-id'));
                                }
                            };
                            
                            input.replaceWith(newSpan);
                        }
                    }).catch(error => {
                        console.error('수정 실패:', error);
                        // 실패시 원래 값으로 복원
                        const restoredSpan = document.createElement('span');
                        restoredSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                        restoredSpan.style.cssText = 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                        restoredSpan.innerText = old;
                        input.replaceWith(restoredSpan);
                    });
                } else if(ev.key==='Escape') {
                    // ESC 키로 취소
                    const cancelSpan = document.createElement('span');
                    cancelSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                    cancelSpan.style.cssText = 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                    cancelSpan.innerText = old;
                    input.replaceWith(cancelSpan);
                }
            };
        };
    }
}