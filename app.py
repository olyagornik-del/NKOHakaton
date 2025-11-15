from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import redirect
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nko.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Post(db.Model):
    __tablename__ = 'NKO'
    id = db.Column(db.Integer, primary_key=True)
    name_nko = db.Column(db.String(300), nullable=False)
    activity = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(300), nullable=False)
    Photo_logo = db.Column(db.Text, nullable=True)
    links = db.Column(db.Text, nullable=True)



# Модель организации
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    website = db.Column(db.String(200))
    social_media = db.Column(db.String(200))
    logo = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=False)  # Модерация
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    organizations = db.relationship('Organization', backref='owner', lazy=True)

# Создаем таблицы
with app.app_context():
    db.create_all()



@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/posts")
def posts():
    posts = Post.query.all()
    return render_template("posts.html", posts=posts)

@app.route("/create", methods=['POST', 'GET'])
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
        return render_template("create.html")


# app.py
@app.route('/api/organizations')
def api_organizations():
    # Получаем параметры фильтрации
    city = request.args.get('city')
    search = request.args.get('search')

    # Базовый запрос - только одобренные организации
    query = Organization.query.filter_by(is_approved=True)

    # Фильтрация по городу
    if city and city != 'all':
        query = query.filter_by(city=city)

    # Поиск по названию
    if search:
        query = query.filter(Organization.name.ilike(f'%{search}%'))

    organizations = query.all()

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
    return jsonify(result)


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
    return render_template('map.html', cities=ROSATOM_CITIES)


# Форма добавления организации
@app.route('/create', methods=['GET', 'POST'])
def create_organization():
    if request.method == 'POST':
        # Обработка формы
        new_org = Organization(
            name=request.form['name'],
            category=request.form['category'],
            description=request.form['description'],
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            city=request.form['city'],
            latitude=request.form.get('latitude', type=float),
            longitude=request.form.get('longitude', type=float),
            website=request.form.get('website'),
            social_media=request.form.get('social_media'),
            is_approved=False  # Ждет модерации
        )

        db.session.add(new_org)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('create.html', cities=ROSATOM_CITIES)

if __name__ == '__main__':
    app.run(debug=True)
