

def get_region_detail_map():
  # 지역 별 세부지역을 담을 배열들 - 주소지 파트에서 사용
  # 서울특별시 내 세부지역
  seoulList = [
    "종로구",
    "중구",
    "용산구",
    "성동구",
    "광진구",
    "동대문구",
    "중랑구",
    "성북구",
    "강북구",
    "도봉구",
    "노원구",
    "은평구",
    "서대문구",
    "마포구",
    "양천구",
    "강서구",
    "구로구",
    "금천구",
    "영등포구",
    "동작구",
    "관악구",
    "서초구",
    "강남구",
    "송파구",
    "강동구",
  ];

  # 부산광역시 내 세부지역
  busanList = [
    "중구",
    "서구",
    "동구",
    "영도구",
    "부산진구",
    "동래구",
    "남구",
    "북구",
    "해운대구",
    "사하구",
    "금정구",
    "강서구",
    "연제구",
    "수영구",
    "사상구",
    "기장군",
  ];

  # 대구광역시 내 세부지역
  daeguList = [
    "중구",
    "동구",
    "서구",
    "남구",
    "북구",
    "수성구",
    "달서구",
    "달성군",
  ];

  # 인천광역시 내 세부지역
  incheonList = [
    "중구",
    "동구",
    "남구",
    "미추홀구",
    "연수구",
    "남동구",
    "부평구",
    "계양구",
    "서구",
    "강화군",
    "옹진군",
  ];

  # 광주광역시 내 세부지역
  gwangjuList = ["동구", "서구", "남구", "북구", "광산구"];

  # 대전광역시 내 세부 지역
  daejeonList = ["동구", "중구", "서구", "유성구", "대덕구"];

  # 울산광역시 내 세부지역
  ulsanList = ["중구", "남구", "동구", "북구", "울주군"];

  # 세종특별자치시 내 세부지역
  sejongList = [
    "조치원읍",
    "금남면",
    "부강면",
    "소정면",
    "연기면",
    "연동면",
    "연서면",
    "장군면",
    "전동면",
    "전의면",
    "고운동",
    "다정동",
    "대평동",
    "도담동",
    "반곡동",
    "보람동",
    "새롬동",
    "소담동",
    "아름동",
    "종촌동",
    "한솔동",
    "해밀동",
  ];

  # 경기도 내 세부지역
  gyeonggiList = [
    "수원시",
    "성남시",
    "고양시",
    "용인시",
    "부천시",
    "안산시",
    "안양시",
    "남양주시",
    "화성시",
    "평택시",
    "의정부시",
    "시흥시",
    "파주시",
    "광명시",
    "김포시",
    "군포시",
    "광주시",
    "이천시",
    "양주시",
    "오산시",
    "구리시",
    "안성시",
    "포천시",
    "의왕시",
    "하남시",
    "여주시",
    "여주군",
    "양평군",
    "동두천시",
    "과천시",
    "가평군",
    "연천군",
  ];

  # 강원도 내 세부지역
  gangwonList = [
    "춘천시",
    "원주시",
    "강릉시",
    "동해시",
    "태백시",
    "속초시",
    "삼척시",
    "홍천군",
    "횡성군",
    "영월군",
    "평창군",
    "정선군",
    "철원군",
    "화천군",
    "양구군",
    "인제군",
    "고성군",
    "양양군",
  ];

  # 충청북도 내 세부지역
  chungBukList = [
    "청주시",
    "충주시",
    "제천시",
    "청원군",
    "보은군",
    "옥천군",
    "영동군",
    "진천군",
    "괴산군",
    "음성군",
    "단양군",
    "증평군",
  ];

  # 충청북도 내 세부지역
  chungNamList = [
    "천안시",
    "공주시",
    "보령시",
    "아산시",
    "서산시",
    "논산시",
    "계룡시",
    "당진시",
    "당진군",
    "금산군",
    "연기군",
    "부여군",
    "서천군",
    "청양군",
    "홍성군",
    "예산군",
    "태안군",
  ];

  # 전라북도 내 세부지역
  jeonBukList = [
    "전주시",
    "군산시",
    "익산시",
    "정읍시",
    "남원시",
    "김제시",
    "완주군",
    "진안군",
    "무주군",
    "장수군",
    "임실군",
    "순창군",
    "고창군",
    "부안군",
  ];

  # 전라북도 내 세부지역
  jeonNamList = [
    "목포시",
    "여수시",
    "순천시",
    "나주시",
    "광양시",
    "담양군",
    "곡성군",
    "구례군",
    "고흥군",
    "보성군",
    "화순군",
    "장흥군",
    "강진군",
    "해남군",
    "영암군",
    "무안군",
    "함평군",
    "영광군",
    "장성군",
    "완도군",
    "진도군",
    "신안군",
  ];

  # 경상북도 내 세부지역
  gyeongBukList = [
    "포항시",
    "경주시",
    "김천시",
    "안동시",
    "구미시",
    "영주시",
    "영천시",
    "상주시",
    "문경시",
    "경산시",
    "군위군",
    "의성군",
    "청송군",
    "영양군",
    "영덕군",
    "청도군",
    "고령군",
    "성주군",
    "칠곡군",
    "예천군",
    "봉화군",
    "울진군",
    "울릉군",
  ];

  # 경상남도 내 세부지역
  gyeongNamList = [
    "창원시",
    "마산시",
    "진주시",
    "진해시",
    "통영시",
    "사천시",
    "김해시",
    "밀양시",
    "거제시",
    "양산시",
    "의령군",
    "함안군",
    "창녕군",
    "고성군",
    "남해군",
    "하동군",
    "산청군",
    "함양군",
    "거창군",
    "합천군",
  ];

  # 제주특별자치도 내 세부지역
  jejuList = [
    "제주시",
    "서귀포시",
  ];

  return {
    "서울": seoulList,
    "부산": busanList,
    "대구": daeguList,
    "인천": incheonList,
    "광주": gwangjuList,
    "대전": daejeonList,
    "울산": ulsanList,
    "세종": sejongList,
    "경기": gyeonggiList,
    "강원": gangwonList,
    "충북": chungBukList,
    "충남": chungNamList,
    "전북": jeonBukList,
    "전남": jeonNamList,
    "경북": gyeongBukList,
    "경남": gyeongNamList,
    "제주": jejuList,
    "all": "all"
  }
