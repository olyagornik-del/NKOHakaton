// static/js/map.js
let map;
let markers = [];

function initMap() {
    // Прямоугольник, который примерно охватывает все города Росатома
    const russiaBounds = [
        [41, 19],   // юго-запад (примерно Юг Европейской России)
        [82, 180]   // северо-восток (Чукотка)
    ];

    // Создаем карту и сразу ограничиваем перемещение Россией
    map = L.map('map', {
        minZoom: 3,
        maxZoom: 10,
        maxBounds: russiaBounds,          // нельзя «улететь» далеко от России
        maxBoundsViscosity: 0.7          // пружинка по краям
    });

    // Подложка OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        subdomains: ['a', 'b', 'c']
    }).addTo(map);

    // Авто-масштаб: показать весь прямоугольник России
    map.fitBounds(russiaBounds);

    // Загружаем организации
    loadOrganizations();
}

// НОВАЯ ФУНКЦИЯ: Объединяем все фильтры
function filterOrganizations() {
    const city = document.getElementById('cityFilter').value;
    const category = document.getElementById('categoryFilter').value;
    const search = document.getElementById('searchInput').value;

    loadOrganizations(city, category, search);
}

// ОБНОВЛЯЕМ ФУНКЦИЮ loadOrganizations
function loadOrganizations(city = 'all', category = 'all', search = '') {
    console.log('Загрузка организаций для города:', city, 'категории:', category);

    // Формируем URL с параметрами
    let url = '/api/organizations';
    const params = new URLSearchParams();

    if (city && city !== 'all') {
        params.append('city', city);
    }

    if (category && category !== 'all') {
        params.append('category', category);
    }

    if (search) {
        params.append('search', search);
    }

    if (params.toString()) {
        url += '?' + params.toString();
    }

    // Показываем загрузку
    showLoadingMessage();

    // Очищаем старые маркеры
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // Загружаем данные
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Получены данные:', data);
            displayOrganizations(data);
        })
        .catch(error => {
            console.error('Ошибка загрузки организаций:', error);
            showErrorMessage('Ошибка загрузки данных');
        });
}

// ОБНОВЛЯЕМ ФУНКЦИЮ filterByCity (делаем её частным случаем общей фильтрации)
function filterByCity(city) {
    filterOrganizations();
}

// ОБНОВЛЯЕМ ФУНКЦИЮ searchOrganizations
function searchOrganizations(query) {
    filterOrganizations();
}

// ОБНОВЛЯЕМ ФУНКЦИЮ debounceSearch
function debounceSearch(query) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if (query.length >= 2 || query.length === 0) {
            filterOrganizations();
        }
    }, 300);
}

function displayOrganizations(data) {
    const organizations = data.organizations;
    const hasOrganizations = data.has_organizations;
    const selectedCity = data.selected_city;
    const selectedCategory = data.selected_category;  // ДОБАВЛЯЕМ

    // Скрываем сообщения
    hideMessages();

    // Создаем кастомную иконку
    const customIcon = L.divIcon({
        className: 'custom-marker',
        html: '<div style="background-color: #007bff; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
        iconSize: [26, 26],
        iconAnchor: [13, 13]
    });

    // Очищаем старые маркеры
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // УЛУЧШАЕМ СООБЩЕНИЕ ОТСУТСТВИЯ ОРГАНИЗАЦИЙ
    if ((selectedCity || selectedCategory) && !hasOrganizations) {
        let message = '';
        if (selectedCity && selectedCategory) {
            message = `В городе <strong>${selectedCity}</strong> по направлению <strong>${selectedCategory}</strong> пока нет зарегистрированных НКО`;
        } else if (selectedCity) {
            message = `В городе <strong>${selectedCity}</strong> пока нет зарегистрированных НКО`;
        } else if (selectedCategory) {
            message = `По направлению <strong>${selectedCategory}</strong> пока нет зарегистрированных НКО`;
        }

        showNoOrganizationsMessage(message);
        return;
    }
    // Добавляем новые маркеры
    organizations.forEach(org => {
        if (org.latitude && org.longitude) {
            const marker = L.marker([org.latitude, org.longitude], { icon: customIcon })
                .bindPopup(`
                    <div class="popup-content">
                        <h3>${org.name}</h3>
                        <p><strong>Город:</strong> ${org.city}</p>
                        <p><strong>Направление:</strong> ${org.category}</p>
                        <p>${org.description || ''}</p>
                        ${org.phone ? `<p><strong>Телефон:</strong> ${org.phone}</p>` : ''}
                        ${org.address ? `<p><strong>Адрес:</strong> ${org.address}</p>` : ''}
                    </div>
                `)
                .addTo(map);
            markers.push(marker);
        }
    });

    // Если есть метки, подстраиваем карту под них
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));

        // УЛУЧШАЕМ СООБЩЕНИЕ УСПЕХА
        let successMessage = `Найдено организаций: ${organizations.length}`;
        if (selectedCategory && selectedCategory !== 'all') {
            successMessage += ` по направлению "${selectedCategory}"`;
        }
        showSuccessMessage(successMessage);

        // Если выбран конкретный город и есть только одна метка - увеличиваем зум
        if (selectedCity && markers.length === 1) {
            setTimeout(() => {
                map.setView(markers[0].getLatLng(), 12);
            }, 500);
        }
    } else if (!selectedCity && !selectedCategory) {
        // Только если не выбраны фильтры
        showInfoMessage('Используйте фильтры для поиска организаций');
    }
}

// ОБНОВЛЯЕМ ФУНКЦИЮ showNoOrganizationsMessage
function showNoOrganizationsMessage(messageText) {
    hideMessages();

    const message = `
        <div class="alert alert-info mt-3" id="noOrgMessage">
            <h5>${messageText}</h5>
            <p class="mb-0">Вы можете стать первым, кто добавит НКО!</p>
        </div>
    `;

    // Добавляем сообщение перед картой
    const mapContainer = document.querySelector('.map-container');
    mapContainer.insertAdjacentHTML('beforebegin', message);

    // Центрируем карту на России
    map.fitBounds([[41, 19], [82, 180]]);
}
function showLoadingMessage() {
    hideMessages();
    const message = '<div class="alert alert-warning mt-3" id="loadingMessage">Загрузка данных...</div>';
    const mapContainer = document.querySelector('.map-container');
    mapContainer.insertAdjacentHTML('beforebegin', message);
}

function showSuccessMessage(text) {
    hideMessages();
    const message = `<div class="alert alert-success mt-3" id="successMessage">${text}</div>`;
    const mapContainer = document.querySelector('.map-container');
    mapContainer.insertAdjacentHTML('beforebegin', message);

    // Автоматически скрываем через 3 секунды
    setTimeout(hideMessages, 3000);
}

function showInfoMessage(text) {
    hideMessages();
    const message = `<div class="alert alert-info mt-3" id="infoMessage">${text}</div>`;
    const mapContainer = document.querySelector('.map-container');
    mapContainer.insertAdjacentHTML('beforebegin', message);
}

function showErrorMessage(text) {
    hideMessages();
    const message = `<div class="alert alert-danger mt-3" id="errorMessage">${text}</div>`;
    const mapContainer = document.querySelector('.map-container');
    mapContainer.insertAdjacentHTML('beforebegin', message);
}

function hideMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach(msg => msg.remove());
}

// Инициализация при загрузке страницы
// document.addEventListener('DOMContentLoaded', initMap);