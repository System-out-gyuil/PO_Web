from solapi import SolapiMessageService
from solapi.model import RequestMessage
from solapi.model.kakao.kakao_option import KakaoOption
from config import SOLAPI_API_KEY, SOLAPI_SECRET_KEY, SEND_NUMBER, KAKAO_PF_ID, KAKAO_SIGNUP_TEMPLATE_ID, KAKAO_USE_DATE_OVER_TEMPLATE_ID


def solapi_api(send_type, to):
  to = to.replace("-", "")

  print(f'send_type: {send_type}, to: {to}')

  if send_type == "signup":
    template_id = KAKAO_SIGNUP_TEMPLATE_ID

  elif send_type == "use_date_over":
    template_id = KAKAO_USE_DATE_OVER_TEMPLATE_ID

  # API 키와 API Secret을 설정합니다
  message_service = SolapiMessageService(
    api_key=SOLAPI_API_KEY, 
    api_secret=SOLAPI_SECRET_KEY
    )


  # 카카오 알림톡 발송을 위한 옵션을 생성합니다.
  kakao_option = KakaoOption(
      pf_id=KAKAO_PF_ID, # 카카오톡 채널 ID
      template_id=template_id, # 템플릿 ID
      # 만약에 템플릿에 변수가 있다면 아래와 같이 설정합니다.
      # 값은 반드시 문자열로 넣어주셔야 합니다!
      # variables={
      #   "#{name}": "홍길동",
      #   "#{age}": "30"
      # }
  )

  # 단일 메시지를 생성합니다
  message = RequestMessage(
      from_=SEND_NUMBER,  # 발신번호 (등록된 발신번호만 사용 가능)
      to=to,  # 수신번호
      kakao_options=kakao_option,
  )

  # 메시지를 발송합니다
  try:
      response = message_service.send(message)
      print("메시지 발송 성공!")
  except Exception as e:
      print(f"메시지 발송 실패: {str(e)}")