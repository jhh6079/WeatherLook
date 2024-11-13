//async function fetchWeatherData() {
//    const serviceKey = "XNyIHsESPOxad%2FeFJBZ6XDBl3nREZZdwEqVbdW%2FLl778zJVP3zPrsJNXkeYnPtPrGyYjQuubBb%2Bf1Pq7ekMU6g%3D%3D"; // 발급받은 API 키 입력
//
//    const today = new Date();
//    const year = today.getFullYear();
//    const month = String(today.getMonth() + 1).padStart(2, '0');
//    const day = String(today.getDate()).padStart(2, '0');
//    const base_date = `${year}${month}${day}`;
//
//    const hours = today.getHours();
//    const minutes = today.getMinutes();
//    let base_time;
//
//    if (minutes >= 40) {
//        base_time = `${String(hours).padStart(2, '0')}30`;
//    } else {
//        base_time = `${String(hours - 1).padStart(2, '0')}30`;
//    }
//
//    const nx = 60;
//    const ny = 127;
//    const url = `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey=${serviceKey}&numOfRows=60&pageNo=1&dataType=json&base_date=${base_date}&base_time=${base_time}&nx=${nx}&ny=${ny}`;
//
//    try {
//        const response = await fetch(url);
//        if (!response.ok) {
//            throw new Error("API 요청 실패 - 상태 코드: " + response.status);
//        }
//        const responseData = await response.text(); // JSON 대신 text로 읽기
//
//        // XML로 응답이 온 경우 파싱
//        if (responseData.startsWith('<')) {
//            const parser = new DOMParser();
//            const xmlDoc = parser.parseFromString(responseData, "application/xml");
//            console.log(xmlDoc); // XML 응답 확인
//
//            // XML 파싱 후 필요한 데이터 추출
//            const errMsg = xmlDoc.querySelector("errMsg")?.textContent;
//            if (errMsg) {
//                throw new Error("API 오류 메시지: " + errMsg);
//            }
//            return;
//        }
//
//        // JSON 파싱 시도
//        const data = JSON.parse(responseData);
//        displayCurrentWeather(data);
//        displayHourlyForecast(data);
//    } catch (error) {
//        console.error("날씨 데이터를 불러오는 중 오류 발생:", error);
//        document.getElementById("temperature").textContent = "데이터 로드 실패";
//    }
//}
//
//// 현재 날씨 데이터를 HTML에 표시하는 함수
//function displayCurrentWeather(data) {
//    const items = data.response.body.items.item;
//    const temperature = items.find(item => item.category === "T1H").fcstValue; // T1H: 기온
//    const humidity = items.find(item => item.category === "REH").fcstValue; // REH: 습도
//    const windSpeed = items.find(item => item.category === "WSD").fcstValue; // WSD: 풍속
//
//    document.getElementById("temperature").textContent = `${temperature}°`;
//    document.getElementById("details").textContent = `온도 ${temperature}° · 습도 ${humidity}% · 바람 ${windSpeed}m/s`;
//}
//
//// 시간대별 날씨 데이터를 HTML에 표시하는 함수
//function displayHourlyForecast(data) {
//    const items = data.response.body.items.item;
//    const forecastContainer = document.getElementById("hourly-forecast");
//    forecastContainer.innerHTML = ''; // 기존 내용 초기화
//
//    // 시간별 기온 정보 필터링
//    const hourlyData = items.filter(item => item.category === "T1H"); // T1H: 기온
//
//    const currentTime = new Date();
//    const currentHour = currentTime.getHours();
//
//    // 현재 시간 기준으로 향후 24시간 데이터 필터링
//    const filteredData = hourlyData.filter(item => {
//        const itemHour = parseInt(item.fcstTime.slice(0, 2), 10);
//        const itemDate = new Date(currentTime);
//        itemDate.setHours(itemHour);
//
//        // 현재 시간부터 24시간 이내인지 확인
//        return (itemDate >= currentTime) && (itemDate < new Date(currentTime.getTime() + 24 * 60 * 60 * 1000));
//    });
//
//    filteredData.forEach(item => {
//        const hourElement = document.createElement("div");
//        hourElement.classList.add("hour");
//        hourElement.textContent = `${item.fcstTime.slice(0, 2)}시: ${item.fcstValue}°`;
//        forecastContainer.appendChild(hourElement);
//    });
//}
//
//
//
//// 페이지 로드 시 날씨 데이터 가져오기
//document.addEventListener("DOMContentLoaded", fetchWeatherData);

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

    // 초단기 실황 API URL
    const ultraSrtFcstUrl = `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey=${serviceKey}&numOfRows=60&pageNo=1&dataType=json&base_date=${base_date}&base_time=${base_time}&nx=${nx}&ny=${ny}`;

    // 단기예보 API URL (1시간 간격 예보)
    const vilageFcstUrl = `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey=${serviceKey}&numOfRows=1000&pageNo=1&dataType=json&base_date=${base_date}&base_time=0200&nx=${nx}&ny=${ny}`;

    try {
        // 초단기 실황 데이터 가져오기
        const ultraSrtFcstResponse = await fetch(ultraSrtFcstUrl);
        if (!ultraSrtFcstResponse.ok) {
            throw new Error("초단기 실황 API 요청 실패 - 상태 코드: " + ultraSrtFcstResponse.status);
        }
        const ultraSrtFcstData = await ultraSrtFcstResponse.json();
        displayCurrentWeather(ultraSrtFcstData);

        // 단기예보 데이터 가져오기
        const vilageFcstResponse = await fetch(vilageFcstUrl);
        if (!vilageFcstResponse.ok) {
            throw new Error("단기예보 API 요청 실패 - 상태 코드: " + vilageFcstResponse.status);
        }
        const vilageFcstData = await vilageFcstResponse.json();
        displayHourlyForecast(vilageFcstData);

    } catch (error) {
        console.error("날씨 데이터를 불러오는 중 오류 발생:", error);
        document.getElementById("temperature").textContent = "데이터 로드 실패";
    }
}

// 현재 날씨 데이터를 HTML에 표시하는 함수 (초단기 실황 데이터 사용)
function displayCurrentWeather(data) {
    const items = data.response.body.items.item;
    const temperature = items.find(item => item.category === "T1H").fcstValue; // T1H: 기온
    const humidity = items.find(item => item.category === "REH").fcstValue; // REH: 습도
    const windSpeed = items.find(item => item.category === "WSD").fcstValue; // WSD: 풍속

    document.getElementById("temperature").textContent = `${temperature}°`;
    document.getElementById("details").textContent = `온도 ${temperature}° · 습도 ${humidity}% · 바람 ${windSpeed}m/s`;
}

// 1시간 단위로 날씨 데이터를 HTML에 표시하는 함수 (단기예보 데이터 사용)
function displayHourlyForecast(data) {
    const items = data.response.body.items.item;
    const forecastContainer = document.getElementById("hourly-forecast");
    forecastContainer.innerHTML = ''; // 기존 내용 초기화

    // TMP 항목을 필터링하여 기온 정보를 가져옵니다.
    const hourlyData = items.filter(item => item.category === "TMP");

    // 24시간 동안의 1시간 단위 데이터를 가져오기
    const currentTime = new Date();
    const futureTime = new Date(currentTime.getTime() + 24 * 60 * 60 * 1000); // 24시간 후

    const filteredData = hourlyData.filter(item => {
        const itemDateTime = new Date(`${item.fcstDate.slice(0, 4)}-${item.fcstDate.slice(4, 6)}-${item.fcstDate.slice(6, 8)}T${item.fcstTime.slice(0, 2)}:00:00`);
        return itemDateTime >= currentTime && itemDateTime <= futureTime;
    });

    // 1시간 단위로 24시간 예보 출력
    filteredData.forEach(item => {
        const hourElement = document.createElement("div");
        hourElement.classList.add("hour");
        hourElement.textContent = `${item.fcstTime.slice(0, 2)}시: ${item.fcstValue}°`;
        forecastContainer.appendChild(hourElement);
    });
}

// 페이지 로드 시 날씨 데이터 가져오기
document.addEventListener("DOMContentLoaded", fetchWeatherData);
