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


function loadOrganizations() {
    fetch('/api/organizations')
        .then(response => response.json())
        .then(organizations => {
            displayOrganizations(organizations);
        })
        .catch(error => console.error('Error:', error));
}

function displayOrganizations(organizations) {
    // Очищаем старые маркеры
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // Добавляем новые маркеры
    organizations.forEach(org => {
        if (org.latitude && org.longitude) {
            const marker = L.marker([org.latitude, org.longitude])
                .bindPopup(`
                    <div class="popup-content">
                        <h3>${org.name}</h3>
                        <p><strong>Город:</strong> ${org.city}</p>
                        <p><strong>Направление:</strong> ${org.category}</p>
                        <p>${org.description || ''}</p>
                        ${org.phone ? `<p><strong>Телефон:</strong> ${org.phone}</p>` : ''}
                        ${org.address ? `<p><strong>Адрес:</strong> ${org.address}</p>` : ''}
                        <a href="/organization/${org.id}" class="btn btn-sm btn-primary">Подробнее</a>
                    </div>
                `)
                .addTo(map);
            markers.push(marker);
        }
    });
}

// Фильтрация по городу
function filterByCity(city) {
    if (city === 'all') {
        loadOrganizations();
    } else {
        fetch(`/api/organizations?city=${city}`)
            .then(response => response.json())
            .then(organizations => {
                displayOrganizations(organizations);
            });
    }
}

// Поиск по названию
function searchOrganizations(query) {
    fetch(`/api/organizations?search=${query}`)
        .then(response => response.json())
        .then(organizations => {
            displayOrganizations(organizations);
        });
}

// Инициализация при загрузке страницы
// document.addEventListener('DOMContentLoaded', initMap);