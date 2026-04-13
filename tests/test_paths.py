from semantic_heap.parser import extract_anchors
from semantic_heap.paths import generate_paths


def test_path_generation_dinner():
    idea = "David is going to dinner tonight"
    path = generate_paths("users", idea, extract_anchors(idea))[0]
    assert path == "users.david.plans.dinner.tonight"


def test_path_generation_spelling_preference():
    idea = "David does not want spelling corrections called out"
    path = generate_paths("users", idea, extract_anchors(idea))[0]
    assert path == "users.david.preferences.spelling.spelling.no_callout"


def test_path_generation_canvas_uwm():
    idea = "Canvas is the LMS used by UWM"
    path = generate_paths("world", idea, extract_anchors(idea))[0]
    assert path == "world.uwm.platforms.canvas"
