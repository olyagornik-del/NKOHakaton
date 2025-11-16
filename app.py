from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import redirect
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nko.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель организации
# Модель организации (ЗАМЕНИТЕ старые модели на эту)
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Основная информация (из ТЗ)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Направление деятельности
    short_description = db.Column(db.Text)  # Краткое описание (2-3 предложения)
    description = db.Column(db.Text)  # Полное описание (из CSV)
    target_audience = db.Column(db.Text)  # Целевая аудитория (из CSV)

    # Контакты (из ТЗ)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    # География
    city = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)  # Широта (будет вычислена автоматически)
    longitude = db.Column(db.Float)  # Долгота (будет вычислена автоматически)

    # Ссылки и медиа (из ТЗ)
    website = db.Column(db.String(200))
    social_media = db.Column(db.Text)  # Может быть несколько ссылок
    logo = db.Column(db.String(200))  # Путь к файлу или ссылка

    # Системные поля
    is_approved = db.Column(db.Boolean, default=False)  # Модерация
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Для будущей авторизации

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    organizations = db.relationship('Organization', backref='owner', lazy=True)

# Создаем таблицы
with app.app_context():
    db.create_all()


@app.route("/organizations")
def organizations():
    # Получаем параметры фильтрации из URL
    city = request.args.get('city', 'all')
    category = request.args.get('category', 'all')

    # Базовый запрос - только одобренные организации
    query = Organization.query.filter_by(is_approved=True)

    # Фильтрация по городу
    if city and city != 'all':
        query = query.filter_by(city=city)

    # Фильтрация по категории
    if category and category != 'all':
        query = query.filter_by(category=category)

    organizations = query.all()

    # Получаем уникальные города и категории для фильтров
    cities = db.session.query(Organization.city).filter_by(is_approved=True).distinct().all()
    categories = db.session.query(Organization.category).filter_by(is_approved=True).distinct().all()

    return render_template(
        "organizations.html",
        organizations=organizations,
        cities=[city[0] for city in cities],
        categories=[category[0] for category in categories],
        selected_city=city,
        selected_category=category
    )

@app.route('/create', methods=['GET', 'POST'])
def create_organization():
    if request.method == 'POST':
        city = request.form['city']

        # Автоматически получаем координаты для выбранного города
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="nko_map_app")
        location = geolocator.geocode(f"{city}, Россия")

        new_org = Organization(
            name=request.form['name'],
            category=request.form['category'],
            short_description=request.form['short_description'],
            description=request.form.get('description'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            city=city,
            latitude=location.latitude if location else None,
            longitude=location.longitude if location else None,
            social_media=request.form.get('social_media'),
            is_approved=False  # Ждет модерации
        )

        db.session.add(new_org)
        db.session.commit()

        return redirect(url_for('map'))

    return render_template('create.html', cities=ROSATOM_CITIES)


# app.py - в функции api_organizations

@app.route('/api/organizations')
def api_organizations():
    # Получаем параметры фильтрации
    city = request.args.get('city')
    category = request.args.get('category')  # ДОБАВЛЯЕМ ЭТУ СТРОЧКУ
    search = request.args.get('search')

    # Базовый запрос - только одобренные организации
    query = Organization.query.filter_by(is_approved=True)

    # Фильтрация по городу
    if city and city != 'all':
        query = query.filter_by(city=city)

    # ФИЛЬТРАЦИЯ ПО КАТЕГОРИИ (ДОБАВЛЯЕМ ЭТОТ БЛОК)
    if category and category != 'all':
        query = query.filter_by(category=category)

    # Поиск по названию
    if search:
        query = query.filter(Organization.name.ilike(f'%{search}%'))

    organizations = query.all()

    # Проверяем, есть ли организации с выбранными фильтрами
    has_organizations = len(organizations) > 0
    selected_city = city if city and city != 'all' else None
    selected_category = category if category and category != 'all' else None  # ДОБАВЛЯЕМ

    # Преобразуем в JSON
    result = []
    for org in organizations:
        result.append({
            'id': org.id,
            'name': org.name,
            'category': org.category,
            'description': org.description,
            'phone': org.phone,
            'address': org.address,
            'city': org.city,
            'latitude': org.latitude,
            'longitude': org.longitude,
            'website': org.website,
            'social_media': org.social_media
        })

    return jsonify({
        'organizations': result,
        'has_organizations': has_organizations,
        'selected_city': selected_city,
        'selected_category': selected_category,  # ДОБАВЛЯЕМ
        'total_count': len(result)
    })


# Главная страница с картой

# app.py
# Список городов из ТЗ
ROSATOM_CITIES = [
    'Ангарск', 'Байкальск', 'Балаково', 'Билибино', 'Волгодонск',
    'Глазов', 'Десногорск', 'Димитровград', 'Железногорск', 'Заречный',
    'Зеленогорск', 'Краснокаменск', 'Курчатов', 'Лесной', 'Неман',
    'Нововоронеж', 'Новоуральск', 'Обнинск', 'Озерск', 'Певек',
    'Полярные Зори', 'Саров', 'Северск', 'Снежинск', 'Советск',
    'Сосновый Бор', 'Трехгорный', 'Удомля', 'Усолье-Сибирское',
    'Электросталь', 'Энергодар'
]


@app.route('/')
def map():
    # ПОЛУЧАЕМ УНИКАЛЬНЫЕ КАТЕГОРИИ ИЗ БАЗЫ ДАННЫХ
    categories = db.session.query(Organization.category).filter_by(is_approved=True).distinct().all()
    categories_list = [cat[0] for cat in categories] if categories else []

    return render_template('map.html', cities=ROSATOM_CITIES, categories=categories_list)


'''@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == "POST":
        name_nko = request.form["name_nko"]
        activity = request.form["activity"]
        contact_phone = request.form["contact_phone"]
        location = request.form["location"]
        Photo_logo = request.form["location"]
        links = request.form["links"]

        post = Post(name_nko=name_nko, activity=activity, contact_phone=contact_phone, location=location, Photo_logo=Photo_logo, links=links)

        try:
            db.session.add(post)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(f"Ошибка: {e}")
            return 'При добавлении НКО произошла ошибка :('
    else:
        return render_template("create.html")'''

'''class Post(db.Model):
    __tablename__ = 'NKO'
    id = db.Column(db.Integer, primary_key=True)
    name_nko = db.Column(db.String(300), nullable=False)
    activity = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(300), nullable=False)
    Photo_logo = db.Column(db.Text, nullable=True)
    links = db.Column(db.Text, nullable=True)'''


'''
@app.route("/posts")
def posts():
    posts = Post.query.all()
    return render_template("posts.html", posts=posts)'''

if __name__ == '__main__':
    app.run(debug=True, port=5001)
