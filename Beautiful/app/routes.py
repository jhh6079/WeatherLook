# app/routes.py
from flask import Blueprint, render_template, request, jsonify, current_app
import requests
from .utils import load_address_data, convert_to_grid, get_clothing_recommendation

# Blueprint 생성
bp = Blueprint('main', __name__)

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

            weather_info = {
                'temperature': temp,
                'wind_speed': wind_speed,
                'sky_status': sky_status_str,
                'precipitation_type': precipitation_type_str,
                'precipitation_probability': precipitation_probability,
                'humidity': humidity
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