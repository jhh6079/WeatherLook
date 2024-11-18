# app/routes.py
import openai
from flask import Blueprint, render_template, request, jsonify, current_app
import requests
from .utils import load_address_data, convert_to_grid, get_clothing_recommendation

# Blueprint 생성
bp = Blueprint('main', __name__)
weather_info = {}
@bp.route('/')
def index():
    address_data = load_address_data()
    return render_template('index.html', address_data=address_data)

@bp.route('/get_coords', methods=['POST'])
def get_coords():
    try:
        data = request.json
        address = f"{data['city']} {data['gu']} {data['dong']}"
        url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
        headers = {"Authorization": f"KakaoAK {current_app.config['KAKAO_API_KEY']}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            documents = response.json().get('documents', [])
            if documents:
                coords = documents[0]
                return jsonify({'lat': coords['y'], 'lon': coords['x']})
            else:
                return jsonify({'error': f'주소를 찾을 수 없습니다: {address}'}), 404
        else:
            return jsonify({'error': f'Kakao API 오류: {response.status_code}'}), 500
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500

@bp.route('/get_weather', methods=['POST'])
def get_weather():
    global weather_info  # 전역 변수 사용
    try:
        data = request.json
        lat, lon = float(data['lat']), float(data['lon'])
        nx, ny = convert_to_grid(lat, lon)


        from datetime import datetime, timedelta
        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        if now.hour < 5:
            base_time = "2300"
            base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        elif now.hour < 11:
            base_time = "0500"
        elif now.hour < 17:
            base_time = "1100"
        elif now.hour < 23:
            base_time = "1700"
        else:
            base_time = "2300"

        if now.minute >= 30:
            forecast_time = (now + timedelta(hours=1)).replace(minute=0).strftime("%H%M")
        else:
            forecast_time = now.replace(minute=0).strftime("%H%M")

        url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        params = {
            "serviceKey": current_app.config['WEATHER_API_KEY'],
            "numOfRows": 100,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
            "fcstTime": forecast_time
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            weather_data = response.json()
            items = weather_data['response']['body']['items']['item']

            temp = next(item['fcstValue'] for item in items if item['category'] == 'TMP')
            wind_speed = next(item['fcstValue'] for item in items if item['category'] == 'WSD')
            sky_status = next(item['fcstValue'] for item in items if item['category'] == 'SKY')
            precipitation_type = next(item['fcstValue'] for item in items if item['category'] == 'PTY')
            precipitation_probability = next(item['fcstValue'] for item in items if item['category'] == 'POP')
            humidity = next(item['fcstValue'] for item in items if item['category'] == 'REH')

            sky_status_map = {'1': "맑음", '3': "구름 많음", '4': "흐림"}
            precipitation_type_map = {'0': "없음", '1': "비", '2': "비/눈", '3': "눈"}
            sky_status_str = sky_status_map.get(sky_status, "알 수 없음")
            precipitation_type_str = precipitation_type_map.get(precipitation_type, "알 수 없음")

            hourly_data = []
            for item in items:
                if item['category'] == 'TMP':  # 기온 데이터만 추출
                    hourly_data.append({
                        "time": item['fcstTime'],  # 예보 시간
                        "temperature": item['fcstValue']  # 기온
                    })

            # 시간별 데이터 정렬
            hourly_data.sort(key=lambda x: x['time'])

            weather_info = {
                'temperature': temp,
                'wind_speed': wind_speed,
                'sky_status': sky_status_str,
                'precipitation_type': precipitation_type_str,
                'precipitation_probability': precipitation_probability,
                'humidity': humidity,
                'hourly': hourly_data

            }

            recommendation = get_clothing_recommendation(
                temp, wind_speed, sky_status_str, precipitation_probability,
                current_app.config['OPENAI_API_KEY']
            )
            weather_info['clothing_recommendation'] = recommendation
            return jsonify(weather_info)
        else:
            return jsonify({'error': 'Weather data not found'}), 404

    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500


@bp.route('/ask_question', methods=['POST'])
def ask_question():
    global weather_info  # 전역 변수 사용
    try:
        data = request.json
        question = data['question']
        # 날씨 정보와 관련된 질문 처리
        additional_info = ""
        if weather_info:
            temperature = weather_info['temperature']
            description = weather_info['sky_status']
            wind_speed = weather_info['wind_speed']
            clothing_recommendation = weather_info['clothing_recommendation']

            # 날씨 정보를 추가 정보로 생성
            additional_info = f"현재 기온은 {temperature}°C, 날씨는 {description}, 바람 속도는 {wind_speed}m/s, 추천 의류: {clothing_recommendation}."
            print(question)
        # OpenAI ChatGPT API 호출하여 질문에 대한 응답 생성
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"당신은 날씨 전문가입니다. {additional_info} 날씨에 따른 적절한 의류를 추천하지만, 이외의 다른 날씨와 관련없는 질문에는 대답하지마.  "},
                {"role": "user", "content": question},
            ]
        )

        answer = response.choices[0].message['content'].strip()
        # response.choices[0].message['content']
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"error": "서버 오류가 발생했습니다."}), 500

@bp.route('/save_clothing', methods=['POST'])
def save_clothing():
    try:
        data = request.json
        clothing = data.get('clothing', '')
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "다음과 같은 지문에서 의류 부분만 골라서 저장해줘.\n\n"
                    "예시 입력:\n"
                    "\"체감 온도가 약 7도 정도로 예상되므로, 더 따뜻하게 입고 싶으시다면 다음과 같은 추가 의류를 고려해보세요:\n"
                    "- 두꺼운 스웨터나 후드티\n"
                    "- 보온성이 높은 패딩 조끼 추가\n"
                    "- 기모가 있는 바지 또는 두꺼운 층의 바지\n"
                    "- 두꺼운 장갑이나 털 장갑으로 손 보호\n"
                    "- 목도리나 머플러를 추가하여 목 부위 보온\"\n\n"

                    "예시 출력:\n"
                    "상의 : 두꺼운 스웨터, 후드티, 패딩 조끼\n"
                    "하의 : 기모 바지, 두꺼운 바지\n"
                    "기타 : 장갑, 목도리, 머플러\n\n"
                    "추가 조건: \"기모가 있는 긴 바지\"라는 항목이 있다면,  '기모 바지' 만 남겨줘.\n"
                    ". '두꺼운 외투'처럼 너무 넓은 범위의 의류 항목은 제외해줘.\n"
                    "\"따뜻한 머플러\"라면 '따뜻한' 같은 형용사도 제외하고 '머플러'만 남겨줘.\n\n"
                    "위와 같은 형식으로 의류 부분만 추출해서 출력해줘    ."

                )},
                {"role": "user", "content": f"{clothing}"},
            ]
        )

        answer = response.choices[0].message['content'].strip()

        if answer:
            # 의류 추천을 저장하지 않고 출력만 하는 부분
            print(f"저장된 의류 추천: \n{answer}")
            return jsonify({"message": "의류 추천이 출력되었습니다."})
        else:
            return jsonify({"message": "출력할 의류 추천이 없습니다."}), 400
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"error": "출력 중 오류가 발생했습니다."}), 500