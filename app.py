from flask import Flask, request, jsonify, render_template
from recommender import get_recommendations, improved_recommendations, hybrid, load_data

app = Flask(__name__)

# Load data when starting the app
data = load_data()
titles = data["titles"]
indices = data["indices"]
cosine_sim_basic = data["cosine_sim_basic"]
smd = data["smd"]
titles_adv = data["titles_adv"]
indices_adv = data["indices_adv"]
cosine_sim_advanced = data["cosine_sim_advanced"]
svd = data["svd"]
id_map = data["id_map"]
indices_map = data["indices_map"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend/basic", methods=["GET"])
def recommend_basic():
    movie = request.args.get("title")
    if movie not in titles.values:
        return jsonify({"error": "Movie not found"}), 404
    recommendations = get_recommendations(movie, titles, indices, cosine_sim_basic).head(10)
    return jsonify(recommendations.tolist())

@app.route("/recommend/improved", methods=["GET"])
def recommend_improved():
    movie = request.args.get("title")
    if movie not in titles_adv.values:
        return jsonify({"error": "Movie not found"}), 404
    recommendations = improved_recommendations(movie, smd, indices_adv, cosine_sim_advanced)
    return jsonify(recommendations.tolist())

@app.route("/recommend/hybrid", methods=["GET"])
def recommend_hybrid_api():
    movie = request.args.get("title")
    user_id = request.args.get("userId", type=int)

    if movie not in titles_adv.values:
        return jsonify({"error": "Movie not found"}), 404

    recommendations = hybrid(user_id, movie, indices_adv, cosine_sim_advanced, smd, id_map, indices_map, svd)
    return jsonify(recommendations.tolist())

if __name__ == "__main__":
    app.run(debug=True)
