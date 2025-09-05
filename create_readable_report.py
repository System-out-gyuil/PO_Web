#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 테스트 결과를 읽기 쉬운 HTML 리포트로 변환
"""

import json
import os
from datetime import datetime

def create_html_report(results):
    """HTML 리포트 생성"""
    total_tests = len(results)
    pass_count = len([r for r in results if r['status'] == 'PASS'])
    fail_count = len([r for r in results if r['status'] == 'FAIL'])
    error_count = len([r for r in results if r['status'] == 'ERROR'])
    
    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>정책자금 추천 엔진 테스트 결과</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }}
        .pass {{ background: #4CAF50; }}
        .fail {{ background: #f44336; }}
        .error {{ background: #ff9800; }}
        .total {{ background: #2196F3; }}
        .test-case {{
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 10px;
            overflow: hidden;
        }}
        .test-header {{
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }}
        .test-content {{
            padding: 20px;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }}
        .status.pass {{ background: #4CAF50; }}
        .status.fail {{ background: #f44336; }}
        .status.error {{ background: #ff9800; }}
        .data-section {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .data-section h4 {{
            margin-top: 0;
            color: #333;
        }}
        .data-item {{
            margin: 5px 0;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .data-item:last-child {{
            border-bottom: none;
        }}
        .results-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .expected, .actual {{
            padding: 15px;
            border-radius: 5px;
        }}
        .expected {{
            background: #e8f5e8;
            border-left: 4px solid #4CAF50;
        }}
        .actual {{
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
        }}
        .fund-item {{
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }}
        .fund-item:last-child {{
            border-bottom: none;
        }}
        .comparison {{
            margin: 20px 0;
            padding: 15px;
            background: #fff3cd;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }}
        .diff {{
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }}
        .only-expected {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .only-actual {{
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
        }}
        .amount-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .amount-card {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }}
        .error-message {{
            padding: 15px;
            background: #ffebee;
            border-radius: 5px;
            border-left: 4px solid #f44336;
            color: #c62828;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 정책자금 추천 엔진 테스트 결과</h1>
            <p>생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>총 테스트</h3>
                <h2>{total_tests}</h2>
            </div>
            <div class="summary-card pass">
                <h3>통과</h3>
                <h2>{pass_count}</h2>
                <p>({(pass_count/total_tests*100):.1f}%)</p>
            </div>
            <div class="summary-card fail">
                <h3>실패</h3>
                <h2>{fail_count}</h2>
                <p>({(fail_count/total_tests*100):.1f}%)</p>
            </div>
            <div class="summary-card error">
                <h3>오류</h3>
                <h2>{error_count}</h2>
                <p>({(error_count/total_tests*100):.1f}%)</p>
            </div>
        </div>
"""
    
    # 각 테스트 케이스 추가
    for result in results:
        status_class = result['status'].lower()
        status_text = {'pass': '✅ 통과', 'fail': '❌ 실패', 'error': '⚠️ 오류'}[status_class]
        
        html += f"""
        <div class="test-case">
            <div class="test-header">
                <h3>{result['test_id']} - {result['description']}</h3>
                <span class="status {status_class}">{status_text}</span>
            </div>
            <div class="test-content">
                <p><strong>테스트 포커스:</strong> {result['test_focus']}</p>
"""
        
        # 입력 조건
        html += f"""
                <div class="data-section">
                    <h4>📋 입력 조건</h4>
                    <div class="data-item">
                        <strong>원본 데이터:</strong>
                        <ul>
"""
        for key, value in result['input_conditions']['original_data'].items():
            if isinstance(value, int) and value > 1000000:
                html += f"<li>{key}: {value:,}원 ({value//100000000}억원)</li>"
            elif isinstance(value, int):
                html += f"<li>{key}: {value:,}</li>"
            else:
                html += f"<li>{key}: {value}</li>"
        
        html += """
                        </ul>
                    </div>
                    <div class="data-item">
                        <strong>변환된 데이터:</strong>
                        <ul>
"""
        for key, value in result['input_conditions']['converted_data'].items():
            if key == 'existing_funds':
                html += f"<li>{key}:"
                for fund_key, fund_value in value.items():
                    if fund_value > 0:
                        html += f"<br>&nbsp;&nbsp;{fund_key}: {fund_value:,}원"
                html += "</li>"
            elif isinstance(value, int) and value > 1000000:
                html += f"<li>{key}: {value:,}원 ({value//100000000}억원)</li>"
            elif isinstance(value, int):
                html += f"<li>{key}: {value:,}</li>"
            else:
                html += f"<li>{key}: {value}</li>"
        
        html += """
                        </ul>
                    </div>
                </div>
"""
        
        # 결과 비교
        html += f"""
                <div class="results-comparison">
                    <div class="expected">
                        <h4>📊 예상 결과</h4>
"""
        for i, expected in enumerate(result['results']['expected'], 1):
            html += f'<div class="fund-item">{i:2d}. {expected}</div>'
        
        html += """
                    </div>
                    <div class="actual">
                        <h4>📊 실제 결과</h4>
"""
        for i, actual in enumerate(result['results']['actual'], 1):
            html += f'<div class="fund-item">{i:2d}. {actual}</div>'
        
        html += """
                    </div>
                </div>
"""
        
        # 비교 결과
        comparison = result['comparison']
        if not comparison['is_match']:
            html += f"""
                <div class="comparison">
                    <h4>🔍 비교 결과</h4>
                    <p><strong>일치 여부:</strong> ❌ 불일치</p>
"""
            if comparison['only_expected']:
                html += f"""
                    <div class="diff only-expected">
                        <strong>🔴 예상에만 있음 ({len(comparison['only_expected'])}개):</strong>
                        <ul>
"""
                for item in comparison['only_expected']:
                    html += f"<li>{item}</li>"
                html += "</ul></div>"
            
            if comparison['only_actual']:
                html += f"""
                    <div class="diff only-actual">
                        <strong>🔵 실제에만 있음 ({len(comparison['only_actual'])}개):</strong>
                        <ul>
"""
                for item in comparison['only_actual']:
                    html += f"<li>{item}</li>"
                html += "</ul></div>"
            
            html += "</div>"
        else:
            html += """
                <div class="comparison">
                    <h4>🔍 비교 결과</h4>
                    <p><strong>일치 여부:</strong> ✅ 일치</p>
                </div>
"""
        
        # 금액 정보
        total_amount = result['results']['total_amount']
        funds_count = result['results']['funds_count']
        html += f"""
                <div class="amount-info">
                    <div class="amount-card">
                        <h4>💰 총 추천 금액</h4>
                        <p>{total_amount:,}원 ({total_amount//100000000}억원)</p>
                    </div>
                    <div class="amount-card">
                        <h4>📊 추천 자금 수</h4>
                        <p>{funds_count}개</p>
                    </div>
                </div>
"""
        
        # 오류 정보
        if 'error' in result:
            html += f"""
                <div class="error-message">
                    <h4>❌ 오류 정보</h4>
                    <p>{result['error']}</p>
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

def main():
    """메인 함수"""
    json_file = 'test_results.json'
    html_file = 'test_results.html'
    
    if not os.path.exists(json_file):
        print(f"❌ {json_file} 파일을 찾을 수 없습니다.")
        print("먼저 test_funding_calculator.py를 실행하여 테스트를 수행하세요.")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print("📄 HTML 리포트 생성 중...")
        html_content = create_html_report(results)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML 리포트가 생성되었습니다: {html_file}")
        print(f"📊 총 {len(results)}개 테스트 케이스 포함")
        
        # 브라우저에서 열기
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(html_file)}')
        print("🌐 브라우저에서 리포트를 열었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
