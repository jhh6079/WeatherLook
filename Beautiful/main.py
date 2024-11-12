import math

from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import openai
from key import KAKAO_API_KEY, OPENAI_API_KEY, WEATHER_API_KEY

app = Flask(__name__)

# Kakao 및 OpenAI API 키 설정

openai.api_key = OPENAI_API_KEY  # OpenAI API 키 설정


def load_address_data():
    df = pd.read_excel("전국_읍면동_주소.xlsx")
    df.columns = ["시/도", "구/군", "읍/면/동"]
    df = df.loc[:, ["시/도", "구/군", "읍/면/동"]]

    address_dict = {}
    for _, row in df.iterrows():
        city = row["시/도"]
        gu = row["구/군"]
        dong = row["읍/면/동"]

        if city not in address_dict:
            address_dict[city] = {}
        if gu not in address_dict[city]:
            address_dict[city][gu] = []
        address_dict[city][gu].append(dong)
    return address_dict


address_data = load_address_data()


@app.route('/')
def index():
    address_data = load_address_data()
    return render_template('index.html', address_data=address_data)


@app.route('/get_coords', methods=['POST'])
def get_coords():
    try:
        data = request.json
        address = f"{data['city']} {data['gu']} {data['dong']}"
        print(f"검색할 주소: {address}")  # 디버깅용 출력

        url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
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


# 전역 변수로 날씨 정보와 추천 의류 저장

import math


def convert_to_grid(lat, lon):
    # 모든 상수를 float으로 설정
    RE = 6371.00877  # 지구 반경(km)
    GRID = 5.0  # 격자 간격(km)
    SLAT1 = 30.0  # 투영 위도1(degree)
    SLAT2 = 60.0  # 투영 위도2(degree)
    OLON = 126.0  # 기준점 경도(degree)
    OLAT = 38.0  # 기준점 위도(degree)
    XO = 43.0  # 기준점 X좌표(GRID)
    YO = 136.0  # 기준점 Y좌표(GRID)

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(math.floor(ra * math.sin(theta) + XO + 0.5))
    ny = int(math.floor(ro - ra * math.cos(theta) + YO + 0.5))
    return nx, ny


weather_info = {}
clothing_recommendation = ""


@app.route('/get_weather', methods=['POST'])
def get_weather():
    global weather_info, clothing_recommendation  # 전역 변수 사용
    try:
        data = request.json
        lat, lon = float(data['lat']), float(data['lon'])  # 위도, 경도를 float로 변환

        # 위도/경도를 격자 좌표로 변환
        nx, ny = convert_to_grid(lat, lon)

        # 현재 날짜와 시간 설정
        from datetime import datetime, timedelta

        # 현재 시간
        now = datetime.now()

        # 오늘 날짜 (기상청 API 형식)
        base_date = now.strftime("%Y%m%d")

        # 현재 시각에 맞는 base_time 설정 (가장 가까운 발표 시각을 기준으로 설정)
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

        # 현재 시간에 가장 가까운 정각을 forecast_time으로 설정
        if now.minute >= 30:
            forecast_time = (now + timedelta(hours=1)).replace(minute=0).strftime("%H%M")
        else:
            forecast_time = now.replace(minute=0).strftime("%H%M")
        print(forecast_time)
        # 기상청 API URL 생성
        url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        params = {
            "serviceKey": WEATHER_API_KEY,
            "numOfRows": 100,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
            "fcstTime": forecast_time  # 가장 가까운 정각으로 설정된 예보 시각
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            weather_data = response.json()
            items = weather_data['response']['body']['items']['item']

            # 필요한 데이터 추출 (TMP, WSD, SKY, PTY, POP, REH)
            temp = next(item['fcstValue'] for item in items if item['category'] == 'TMP')
            wind_speed = next(item['fcstValue'] for item in items if item['category'] == 'WSD')
            sky_status = next(item['fcstValue'] for item in items if item['category'] == 'SKY')
            precipitation_type = next(item['fcstValue'] for item in items if item['category'] == 'PTY')
            precipitation_probability = next(item['fcstValue'] for item in items if item['category'] == 'POP')
            humidity = next(item['fcstValue'] for item in items if item['category'] == 'REH')
            sky_status_map = {
                '1': "맑음",
                '3': "구름 많음",
                '4': "흐림",
                '5': "빗방울",
                '6': "빗방울눈날림",
                '7': "눈날림"
            }
            precipitation_type_map = {
                '0': "없음",
                '1': "비",
                '2': "비/눈",
                '3': "눈"
            }
            sky_status_str = sky_status_map.get(sky_status, "알 수 없음")
            precipitation_type_str = precipitation_type_map.get(precipitation_type, "알 수 없음")

            # TMP: 기온 (섭씨 단위)
            # •	WSD: 풍속 (m/s)
            # •	SKY: 하늘 상태 (1: 맑음, 3: 구름 많음, 4: 흐림,5 빗방울 6 빗방울눈날림 7눈날림)
            # •	PTY: 강수 형태 (0: 없음, 1: 비, 2: 비/눈, 3: 눈)
            # •	POP: 강수 확률 (%)
            # •	REH: 습도 (%)
            # •	SNO: 적설 상태
            # 추출한 정보를 JSON 형태로 반환

            weather_info = {
                'temperature': temp,  # 기온
                'wind_speed': wind_speed,  # 풍속
                'sky_status': sky_status_str,  # 하늘 상태
                'precipitation_type': precipitation_type_str,  # 강수 형태
                'precipitation_probability': precipitation_probability,  # 강수 확률
                'humidity': humidity  # 습도
            }
            print(weather_info)
            print(weather_data)

            recommendation = get_clothing_recommendation(temp, wind_speed, sky_status_str, precipitation_probability)
            weather_info['clothing_recommendation'] = recommendation
            print(weather_data)

            return jsonify(weather_info)
        else:
            return jsonify({'error': 'Weather data not found'}), 404

    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500


def get_clothing_recommendation(temp, wind_speed, sky_status_str, precipitation_probability):
    prompt = (
        f"현재 온도는 {temp}도이고, 풍속은 {wind_speed} m/s 이야 날씨는{sky_status_str}이고 강수확률은 {precipitation_probability}%야 "
        "설명은 말고 체감 온도만 보여주고 체감온도에 맞는 적절한 의류를 추천해줘"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 날씨 전문가입니다. 날씨에 따른 적절한 의류를 추천합니다."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message['content']


@app.route('/ask_question', methods=['POST'])
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

@app.route('/save_clothing', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
