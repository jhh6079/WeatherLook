async function fetchWeatherData() {
    const serviceKey = "XNyIHsESPOxad%2FeFJBZ6XDBl3nREZZdwEqVbdW%2FLl778zJVP3zPrsJNXkeYnPtPrGyYjQuubBb%2Bf1Pq7ekMU6g%3D%3D"; // 발급받은 API 키 입력

    // 오늘 날짜와 시간을 base_date와 base_time으로 설정
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const base_date = `${year}${month}${day}`;

    // 현재 시간을 기준으로 base_time 설정
    const hours = today.getHours();
    const minutes = today.getMinutes();
    let base_time;

    // 초단기 예보는 매시각 40분마다 갱신 (ex: 02:40, 03:40 등)
    if (minutes >= 40) {
        base_time = `${String(hours).padStart(2, '0')}30`;
    } else {
        base_time = `${String(hours - 1).padStart(2, '0')}30`;
    }

    // 서울의 격자 좌표
    const nx = 60;
    const ny = 127;

    // 초단기 예보 URL로 수정
    const url = `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey=${serviceKey}&numOfRows=60&pageNo=1&dataType=json&base_date=${base_date}&base_time=${base_time}&nx=${nx}&ny=${ny}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("API 요청 실패 - 상태 코드: " + response.status);
        }
        const data = await response.json();
        displayCurrentWeather(data);
    } catch (error) {
        console.error("날씨 데이터를 불러오는 중 오류 발생:", error);
        document.getElementById("temperature").textContent = "데이터 로드 실패";
    }
}

// 날씨 데이터를 HTML에 표시하는 함수
function displayCurrentWeather(data) {
    const items = data.response.body.items.item;

    // 기온, 습도, 바람 속도 찾기
    const temperature = items.find(item => item.category === "T1H").fcstValue; // T1H: 기온
    const humidity = items.find(item => item.category === "REH").fcstValue; // REH: 습도
    const windSpeed = items.find(item => item.category === "WSD").fcstValue; // WSD: 풍속

    document.getElementById("temperature").textContent = `${temperature}°`;
    document.getElementById("details").textContent = `온도 ${temperature}° · 습도 ${humidity}% · 바람 ${windSpeed}m/s`;
}

// 페이지 로드 시 날씨 데이터 가져오기
document.addEventListener("DOMContentLoaded", fetchWeatherData);