async function fetchWeatherData() {
    const serviceKey = "XNyIHsESPOxad%2FeFJBZ6XDBl3nREZZdwEqVbdW%2FLl778zJVP3zPrsJNXkeYnPtPrGyYjQuubBb%2Bf1Pq7ekMU6g%3D%3D"; // 발급받은 API 키 입력

    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const base_date = `${year}${month}${day}`;

    const hours = today.getHours();
    const minutes = today.getMinutes();
    let base_time;

    if (minutes >= 40) {
        base_time = `${String(hours).padStart(2, '0')}30`;
    } else {
        base_time = `${String(hours - 1).padStart(2, '0')}30`;
    }

    const nx = 60;
    const ny = 127;
    const url = `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey=${serviceKey}&numOfRows=60&pageNo=1&dataType=json&base_date=${base_date}&base_time=${base_time}&nx=${nx}&ny=${ny}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("API 요청 실패 - 상태 코드: " + response.status);
        }
        const responseData = await response.text(); // JSON 대신 text로 읽기
        console.log(responseData); // 응답 내용을 출력하여 확인

        // JSON 파싱 시도
        const data = JSON.parse(responseData);
        displayCurrentWeather(data);
        displayHourlyForecast(data);
    } catch (error) {
        console.error("날씨 데이터를 불러오는 중 오류 발생:", error);
        document.getElementById("temperature").textContent = "데이터 로드 실패";
    }
}

// 현재 날씨 데이터를 HTML에 표시하는 함수
function displayCurrentWeather(data) {
    const items = data.response.body.items.item;
    const temperature = items.find(item => item.category === "T1H").fcstValue; // T1H: 기온
    const humidity = items.find(item => item.category === "REH").fcstValue; // REH: 습도
    const windSpeed = items.find(item => item.category === "WSD").fcstValue; // WSD: 풍속

    document.getElementById("temperature").textContent = `${temperature}°`;
    document.getElementById("details").textContent = `온도 ${temperature}° · 습도 ${humidity}% · 바람 ${windSpeed}m/s`;
}

// 시간대별 날씨 데이터를 HTML에 표시하는 함수
function displayHourlyForecast(data) {
    const items = data.response.body.items.item;
    const forecastContainer = document.getElementById("hourly-forecast");
    forecastContainer.innerHTML = ''; // 기존 내용 초기화

    // 시간별 기온 정보 필터링 및 표시
    const hourlyData = items.filter(item => item.category === "T1H"); // T1H: 기온

    hourlyData.forEach(item => {
        const hourElement = document.createElement("div");
        hourElement.classList.add("hour");
        hourElement.textContent = `${item.fcstTime.slice(0, 2)}시: ${item.fcstValue}°`;
        forecastContainer.appendChild(hourElement);
    });
}

// 페이지 로드 시 날씨 데이터 가져오기
document.addEventListener("DOMContentLoaded", fetchWeatherData);
