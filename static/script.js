// Load popular cities on startup
document.addEventListener('DOMContentLoaded', () => {
    loadPopularCities();

    // Allow Enter to search
    document.getElementById('cityInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            generateMap();
        }
    });
});

async function loadPopularCities() {
    try {
        const response = await fetch('/api/popular-cities');
        const data = await response.json();

        const container = document.getElementById('popularCitiesList');
        container.innerHTML = '';

        data.cities.forEach(city => {
            const btn = document.createElement('button');
            btn.className = 'city-btn' + (city.ready ? ' ready' : '');
            btn.textContent = city.name;
            btn.onclick = () => {
                document.getElementById('cityInput').value = city.name;
                generateMap();
            };
            container.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading popular cities:', error);
        document.getElementById('popularCitiesList').innerHTML =
            '<div class="loading">Error loading cities</div>';
    }
}

async function generateMap() {
    const cityInput = document.getElementById('cityInput');
    const city = cityInput.value.trim();

    if (!city) {
        showMessage('Please enter a city name', 'error');
        return;
    }

    // Disable button and show loading
    const btn = document.getElementById('searchBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');

    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';

    showMessage('Generating map... This may take a few minutes.', 'info');

    try {
        const response = await fetch('/api/generate-map', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ city: city })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error generating map');
        }

        const data = await response.json();

        // Show success message
        const cacheMsg = data.cached ? ' (loaded from cache)' : '';
        showMessage(data.message + cacheMsg, 'success');

        // Show map
        displayMap(data.city, data.map_url);

        // Reload popular cities list
        loadPopularCities();

    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    } finally {
        // Re-enable button
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

function displayMap(city, mapUrl) {
    const container = document.getElementById('mapContainer');
    const title = document.getElementById('mapTitle');
    const frame = document.getElementById('mapFrame');

    title.textContent = city;
    frame.src = mapUrl;
    container.style.display = 'block';

    // Smooth scroll to map
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeMap() {
    const container = document.getElementById('mapContainer');
    container.style.display = 'none';
    document.getElementById('mapFrame').src = '';
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = 'message ' + type;

    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

