from flask import Flask, request, render_template
from recommender import load_data, get_recommendations

app = Flask(__name__)

# Load data once at server start
data = load_data()

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    movie = None

    if request.method == 'POST':
        movie = request.form['movie']
        try:
            # Call recommender with loaded data
            recommendations = get_recommendations(
                movie,
                data['titles'],
                data['indices'],
                data['cosine_sim_basic']
            ).head(10).tolist()
        except:
            recommendations = ["Movie not found or error occurred."]

    return render_template('index.html', recommendations=recommendations, movie=movie)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
