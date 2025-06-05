from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from langchain_openai import ChatOpenAI
from config import OPEN_AI_API_KEY

class BlogView(View):
    def get(self, request):
        return render(request, 'naver_blog/naver_blog.html')

@method_decorator(csrf_exempt, name='dispatch')
class BlogGPTAPIView(View):
    def post(self, request):
        body = json.loads(request.body)
        user_input = body.get("input", "").strip()

        datas = 1

        text = f'dd'

        llm = ChatOpenAI(
            temperature=0,
            model_name='gpt-4.1-mini',
            openai_api_key=OPEN_AI_API_KEY
        )

        user_input = text + datas

        response = llm.invoke(user_input)
        content = response.content.replace("**", "").replace("#", "").strip()
        print("[GPT 응답 원본]:", content)

        return JsonResponse({"response": content})


class BlogWriteView(View):
    def post(self, request):
        print("블로그 작성 요청")
        return render(request, 'naver_blog/naver_blog.html')