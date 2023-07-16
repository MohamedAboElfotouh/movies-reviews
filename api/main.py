from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

IMG_PATH = "https://image.tmdb.org/t/p/original"
URL_SEARCH = "https://api.themoviedb.org/3/search/movie"
URL_ADD = "https://api.themoviedb.org/3/movie/"
API_KEY = "97e7fe3a95929606b1a0846891812813"
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5N2U3ZmUzYTk1OTI5NjA2YjFhMDg0Njg5MTgxMjgxMyIsInN1YiI6IjY0OGY0NGYyYzNjODk" \
            "xMDBlYjMzNDY4OSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.fNrZBkjWOCYtEYktbjgGbOkZgDQU5RHAlL-WdkFn" \
            "F8o"

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

app = Flask(__name__)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db.init_app(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


class EditForm(FlaskForm):
    rating = StringField('Your Rating Out Of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie)).scalars().all()
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    edit_form = EditForm()
    if edit_form.validate_on_submit():
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
        movie_to_update.rating = edit_form.rating.data
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form)


@app.route("/delete/<int:id>")
def delete(id):
    movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        params = {
            "query": add_form.title.data
        }

        response = requests.get(URL_SEARCH, headers=headers, params=params)
        return render_template("select.html", movies=response.json()["results"])
    return render_template("add.html", form=add_form)


@app.route("/add_to_home/<int:id>")
def add_to_home(id):
    my_url = f"{URL_ADD}{id}"
    response = requests.get(my_url, headers=headers).json()
    if not db.session.query(db.exists().where(Movie.description == response["overview"])).scalar():
        new_movie = Movie(
            title=response["original_title"],
            year=int(response["release_date"][0:4]),
            description=response["overview"],
            img_url=f"{IMG_PATH}{response['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))
    return render_template("exists.html")


if __name__ == '__main__':
    app.run(debug=True)
