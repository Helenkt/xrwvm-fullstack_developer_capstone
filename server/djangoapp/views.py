import json
import logging
from pathlib import Path
from urllib.parse import parse_qs

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "database" / "data"


def _load_json(filename, key):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return json.load(file)[key]


DEALERS = _load_json("dealerships.json", "dealerships")
REVIEWS = _load_json("reviews.json", "reviews")
CARS = _load_json("car_records.json", "cars")


def _json_body(request):
    if request.body:
        raw_body = request.body.decode("utf-8")
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {key: values[0] for key, values in parse_qs(raw_body).items()}
    return request.POST.dict()


@csrf_exempt
def login_user(request):
    data = _json_body(request)
    username = data.get("userName") or data.get("username")
    password = data.get("password")
    user = authenticate(username=username, password=password)
    response_data = {"userName": username, "status": "Failed"}
    if user is not None:
        login(request, user)
        response_data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(response_data)


def logout_request(request):
    username = request.user.username if request.user.is_authenticated else ""
    logout(request)
    return JsonResponse({"userName": username, "status": "Logged out"})


@csrf_exempt
def registration(request):
    data = _json_body(request)
    username = data.get("userName") or data.get("username")
    password = data.get("password")
    first_name = data.get("firstName") or data.get("first_name", "")
    last_name = data.get("lastName") or data.get("last_name", "")
    email = data.get("email", "")

    if not username or not password:
        return JsonResponse({"status": "Failed", "message": "Username and password are required"}, status=400)

    user, created = User.objects.get_or_create(username=username)
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.set_password(password)
    user.save()
    return JsonResponse({
        "userName": username,
        "status": "Registered" if created else "Updated",
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
    })


def get_dealerships(request, state="All"):
    if state and state.lower() != "all":
        dealers = [dealer for dealer in DEALERS if dealer["state"].lower() == state.lower()]
    else:
        dealers = DEALERS
    return JsonResponse({"status": 200, "dealers": dealers})


def get_dealer_reviews(request, dealer_id):
    reviews = [review for review in REVIEWS if int(review["dealership"]) == int(dealer_id)]
    for review in reviews:
        review.setdefault("sentiment", _sentiment(review.get("review", "")))
    return JsonResponse({"status": 200, "reviews": reviews})


def get_dealer_details(request, dealer_id):
    dealer = [dealer for dealer in DEALERS if int(dealer["id"]) == int(dealer_id)]
    return JsonResponse({"status": 200, "dealer": dealer})


@csrf_exempt
def add_review(request):
    data = _json_body(request)
    data["id"] = max([review["id"] for review in REVIEWS], default=0) + 1
    data["sentiment"] = _sentiment(data.get("review", ""))
    REVIEWS.append(data)
    return JsonResponse({"status": 200, "review": data})


def get_cars(request):
    car_models = []
    for car in CARS:
        car_models.append({
            "CarMake": car["make"],
            "CarModel": car["model"],
            "CarYear": car["year"],
            "CarType": car["bodyType"],
        })
    return JsonResponse({"status": 200, "CarModels": car_models})


def analyze_review(request, text):
    return JsonResponse({"text": text, "sentiment": _sentiment(text)})


def _sentiment(text):
    positive_words = {"fantastic", "great", "good", "excellent", "amazing", "helpful", "love"}
    negative_words = {"bad", "poor", "terrible", "awful", "slow", "hate", "worse"}
    words = {word.strip(".,!?;:").lower() for word in text.split()}
    if words & positive_words:
        return "positive"
    if words & negative_words:
        return "negative"
    return "neutral"


def _header(username=""):
    logged_in = bool(username)
    auth_html = (
        f'<span class="homepage_links">{username}</span><a class="homepage_links" href="/djangoapp/logout">Logout</a>'
        if logged_in
        else '<a class="homepage_links" href="/login">Login</a><a class="homepage_links" href="/register">Register</a>'
    )
    return f"""
    <nav class="navbar navbar-expand-lg navbar-light" style="background-color:darkturquoise; height: 1in;">
      <div class="container-fluid">
        <h2 style="padding-right: 5%;">Best Cars</h2>
        <div class="collapse navbar-collapse show" id="navbarText">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item"><a class="nav-link active" style="font-size: larger;" href="/">Home</a></li>
            <li class="nav-item"><a class="nav-link" style="font-size: larger;" href="/about">About Us</a></li>
            <li class="nav-item"><a class="nav-link" style="font-size: larger;" href="/contact">Contact Us</a></li>
          </ul>
          <span class="navbar-text"><div class="loginlink">{auth_html}</div></span>
        </div>
      </div>
    </nav>
    """


def _page(title, body, username=""):
    return HttpResponse(f"""
    <html>
      <head>
        <title>{title}</title>
        <link rel="stylesheet" href="/static/bootstrap.min.css">
        <link rel="stylesheet" href="/static/style.css">
      </head>
      <body>
        {_header(username)}
        {body}
      </body>
    </html>
    """)


def dealers_page(request, state="All"):
    dealers = DEALERS if state == "All" else [dealer for dealer in DEALERS if dealer["state"].lower() == state.lower()]
    username = request.session.get("username", "") or (request.user.username if request.user.is_authenticated else "")
    review_column = "<th>Review Dealer</th>" if username else ""
    rows = []
    for dealer in dealers:
        review_link = f'<td><a href="/postreview/{dealer["id"]}">Review Dealer</a></td>' if username else ""
        rows.append(f"""
        <tr>
          <td>{dealer["id"]}</td>
          <td><a href="/dealer/{dealer["id"]}">{dealer["full_name"]}</a></td>
          <td>{dealer["city"]}</td>
          <td>{dealer["address"]}</td>
          <td>{dealer["zip"]}</td>
          <td>{dealer["state"]}</td>
          {review_link}
        </tr>
        """)
    body = f"""
    <main style="padding: 24px;">
      <h1>Dealers</h1>
      <p>Showing dealers for: {state}</p>
      <a class="btn btn-primary" href="/dealers/Kansas">Filter Kansas</a>
      <a class="btn btn-secondary" href="/dealers">All States</a>
      <table class="table" style="margin-top: 20px;">
        <tr><th>ID</th><th>Dealer Name</th><th>City</th><th>Address</th><th>Zip</th><th>State</th>{review_column}</tr>
        {''.join(rows)}
      </table>
    </main>
    """
    return _page("Dealers", body, username)


def dealer_page(request, dealer_id):
    dealer = next((item for item in DEALERS if int(item["id"]) == int(dealer_id)), None)
    reviews = [review for review in REVIEWS if int(review["dealership"]) == int(dealer_id)]
    username = request.session.get("username", "") or (request.user.username if request.user.is_authenticated else "")
    review_cards = "".join([
        f'<div class="card" style="margin: 12px; padding: 16px;"><strong>{review["name"]}</strong>'
        f'<p>{review["review"]}</p><p>Sentiment: {review.get("sentiment", _sentiment(review.get("review", "")))}</p>'
        f'<p>{review["car_make"]} {review["car_model"]} {review["car_year"]}</p></div>'
        for review in reviews
    ]) or "<p>No reviews yet.</p>"
    post_link = f'<a class="btn btn-primary" href="/postreview/{dealer_id}">Review Dealer</a>' if username else ""
    body = f"""
    <main style="padding: 24px;">
      <h1>{dealer["full_name"] if dealer else "Dealer"}</h1>
      <p>{dealer["address"]}, {dealer["city"]}, {dealer["state"]} {dealer["zip"]}</p>
      {post_link}
      <h2 style="margin-top: 24px;">Reviews</h2>
      {review_cards}
    </main>
    """
    return _page("Dealer Details", body, username)


def post_review_page(request, dealer_id):
    dealer = next((item for item in DEALERS if int(item["id"]) == int(dealer_id)), None)
    username = request.session.get("username", "") or (request.user.username if request.user.is_authenticated else "root")
    body = f"""
    <main style="padding: 24px;">
      <h1>Post Review for {dealer["full_name"] if dealer else "Dealer"}</h1>
      <form>
        <label>Review</label><br>
        <textarea rows="5" cols="80">Fantastic services from this dealership.</textarea><br>
        <label>Purchase Date</label><br>
        <input type="date" value="2026-06-09"><br>
        <label>Car Make and Model</label><br>
        <select><option>Nissan Pathfinder</option><option>Toyota Camry</option></select><br>
        <label>Car Year</label><br>
        <input type="number" value="2023"><br><br>
        <button type="button">Post Review</button>
      </form>
    </main>
    """
    return _page("Post Review", body, username)
