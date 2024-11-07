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
# 전역 변수로 날씨 정보와 추천 의류 저장
weather_info = {}
clothing_recommendation = ""


@app.route('/get_weather', methods=['POST'])
def get_weather():
    global weather_info, clothing_recommendation  # 전역 변수 사용
    try:
        data = request.json
        lat, lon = data['lat'], data['lon']

        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url)

        if response.status_code == 200:
            weather_data = response.json()
            temp = weather_data['main']['temp']
            wind_speed = weather_data['wind']['speed']

            # 추천 의류 생성
            clothing_recommendation = get_clothing_recommendation(temp, wind_speed)
            weather_data['clothing_recommendation'] = clothing_recommendation

            # 날씨 정보를 전역 변수에 저장
            weather_info = {
                'temperature': temp,
                'description': weather_data['weather'][0]['description'],
                'wind_speed': wind_speed,
                'clothing_recommendation': clothing_recommendation
            }

            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Weather data not found'}), 404

    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500


def get_clothing_recommendation(temp, wind_speed):
    prompt = (
        f"현재 온도는 {temp}도이고, 풍속은 {wind_speed} m/s 이야 "
        "설명은 말고 체감 온도만 보여주고 체감온도에 맞는 적절한 의류를 추천해줘"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 날씨 전문가입니다."},
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
            description = weather_info['description']
            wind_speed = weather_info['wind_speed']
            clothing_recommendation = weather_info['clothing_recommendation']

            # 날씨 정보를 추가 정보로 생성
            additional_info = f"현재 기온은 {temperature}°C, 날씨는 {description}, 바람 속도는 {wind_speed}m/s, 추천 의류: {clothing_recommendation}."
            print(question)
        # OpenAI ChatGPT API 호출하여 질문에 대한 응답 생성
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"당신은 날씨 전문가입니다. {additional_info}"},
                {"role": "user", "content": question},
            ]
        )
        answer = response.choices[0].message['content'].strip()
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"error": "서버 오류가 발생했습니다."}), 500

if __name__ == '__main__':
    app.run(debug=True)
