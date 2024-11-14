// static/js/script.js

let clothingRecommendation = "";
let lastAnswer = "";
console.log(addressData);  // 콘솔에 데이터 출력

function updateGu() {
    const city = document.getElementById("city").value;
    const guSelect = document.getElementById("gu");
    guSelect.innerHTML = "<option value=''>구/군 선택</option>";

    if (addressData[city]) {
        Object.keys(addressData[city]).forEach(gu => {
            const option = document.createElement("option");
            option.value = gu;
            option.textContent = gu;
            guSelect.appendChild(option);
        });
    }
    document.getElementById("dong").innerHTML = "<option value=''>읍/면/동 선택</option>";
}

function updateDong() {
    const city = document.getElementById("city").value;
    const gu = document.getElementById("gu").value;
    const dongSelect = document.getElementById("dong");
    dongSelect.innerHTML = "<option value=''>읍/면/동 선택</option>";

    if (addressData[city] && addressData[city][gu]) {
        addressData[city][gu].forEach(dong => {
            const option = document.createElement("option");
            option.value = dong;
            option.textContent = dong;
            dongSelect.appendChild(option);
        });
    }
}

async function getWeather() {
    const city = document.getElementById("city").value;
    const gu = document.getElementById("gu").value;
    const dong = document.getElementById("dong").value;

    if (!city || !gu || !dong) {
        alert("모든 항목을 선택해 주세요.");
        return;
    }

    const button = document.querySelector("button");
    button.disabled = true;
    button.textContent = "조회 중...";

    try {
        const coordsResponse = await fetch('/get_coords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ city, gu, dong })
        });

        const coordsData = await coordsResponse.json();
        if (coordsResponse.ok) {
            const { lat, lon } = coordsData;
            const weatherResponse = await fetch('/get_weather', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat, lon })
            });

            const weatherData = await weatherResponse.json();
            if (weatherResponse.ok) {
                hideSelectionUI();
                clothingRecommendation = weatherData.clothing_recommendation;
                displayResult(city, gu, dong, lat, lon, weatherData);

                const chatButton = document.querySelector(".open-chat-btn");
                const chatSidebar = document.getElementById("chatSidebar");
                chatButton.style.display = "block";
                chatSidebar.style.display = "block";

            } else {
                alert(weatherData.error);
            }
        } else {
            alert(coordsData.error);
        }
    } catch (error) {
        console.error("오류 발생:", error);
        alert("서버와의 통신 중 오류가 발생했습니다.");
    } finally {
        button.disabled = false;
        button.textContent = "조회";
    }
}

function hideSelectionUI() {
    document.getElementById("city").style.display = "none";
    document.getElementById("gu").style.display = "none";
    document.getElementById("dong").style.display = "none";
    document.querySelector("button").style.display = "none";
}

function displayResult(city, gu, dong, lat, lon, weatherData) {
    const resultDiv = document.querySelector(".result");
    resultDiv.style.display = "block";
    resultDiv.style.opacity = "1";

    const formattedClothingRecommendation = weatherData.clothing_recommendation
        .split('\n')
        .map(line =>
            line.replace(/:/g, ':<br>')
                .replace(/,/g, ',<br>')
                .replace(/- /g, '<br>- ')
        )
        .join('<br>');

    resultDiv.innerHTML = `
    <div class="box">
      <h2>선택된 위치</h2>
      <p>${city} > ${gu} > ${dong}</p>
      <p>위도: ${lat}<br> 경도: ${lon}</p>
    </div>
    <div class="box">
      <h2>날씨 정보</h2>
      <p>온도: ${weatherData.temperature}°C</p>
      <p>날씨 상태: ${weatherData.sky_status}</p>
      <p>풍속: ${weatherData.wind_speed} m/s</p>
      <p>강수 형태: ${weatherData.precipitation_type}</p>
      <p>강수 확률: ${weatherData.precipitation_probability}%</p>
      <p>습도: ${weatherData.humidity}%</p>
    </div>
    <div class="box">
      <h2>추천 의류</h2>
      <p>${formattedClothingRecommendation}</p>
    </div>
  `;
}

function toggleChat() {
    const chatSidebar = document.getElementById("chatSidebar");
    const chatButton = document.querySelector(".open-chat-btn");
    const overlay = document.getElementById("overlay");
    const body = document.body;

    if(chatSidebar.style.right === "0px") {
        chatSidebar.style.right = "-100%";
        chatButton.innerHTML = '<i class="fa fa-comments"></i>';
        overlay.style.display = "none";
        body.classList.remove("blurred");
    } else {
        chatSidebar.style.right = "0px";
        chatButton.innerHTML = '<i class="fa fa-home"></i>';
        overlay.style.display = "block";
        body.classList.add("blurred");
    }
}

async function askQuestion() {
    const userQuestion = document.getElementById("userQuestion").value;
    const chatResponse = document.getElementById("chatResponse");

    if (!userQuestion) {
        alert("질문을 입력해 주세요.");
        return;
    }

    const userBubble = document.createElement("p");
    userBubble.className = "user";
    userBubble.innerHTML = `<span>${userQuestion}</span>`;
    chatResponse.appendChild(userBubble);

    document.getElementById("userQuestion").value = "";

    try {
        const response = await fetch('/ask_question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userQuestion })
        });

        const data = await response.json();
        lastAnswer = data.answer;

        const botBubble = document.createElement("p");
        botBubble.className = "bot";
        botBubble.innerHTML = `<span>${data.answer}</span>`;
        chatResponse.appendChild(botBubble);

    } catch (error) {
        console.error("오류 발생:", error);
        const errorBubble = document.createElement("p");
        errorBubble.className = "bot";
        errorBubble.innerHTML = `<span>오류가 발생했습니다. 다시 시도해 주세요.</span>`;
        chatResponse.appendChild(errorBubble);
    }
    chatResponse.scrollTop = chatResponse.scrollHeight;
}

window.onload = function() {
    const citySelect = document.getElementById("city");
    Object.keys(addressData).forEach(city => {
        if (city !== "Column3") {
            const option = document.createElement("option");
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        }
    });

    citySelect.addEventListener("change", updateGu);
    document.getElementById("gu").addEventListener("change", updateDong);
};

function saveClothing() {
    fetch('/save_clothing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clothing: lastAnswer })
    })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error('오류 발생:', error));
}