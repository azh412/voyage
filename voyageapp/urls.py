from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register_view, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("initialize_interests", views.add_topics_to_user, name='initialize_interests'),
    path("itlt", views.generate_titles_onboarding, name='itlt'),
    path("save_likes", views.save_likes, name='save_likes'),
    path("gettitles", views.generate_titles_onboarded, name='generate_titles_onboarded'),
    path("create_lesson", views.generate_lesson, name='create_lesson'),
    path("lesson_feedback", views.feedback, name="lesson_feedback"),
    path("search", views.search, name="search"),
    path("administrator", views.admin, name="admin"),
    path("getusers", views.getusers, name='getusers'),
    path("expeditions", views.expeditions, name='expeditions'),
    path("expeditions/<int:expedition_id>", views.getexpedition, name='getexpedition'),
    path("startexpedition", views.startexpedition, name='startexpedition'),
    path("createexpedition", views.createexpedition, name='createexpedition'),
    path("create_lesson_expd", views.createexpeditionlesson, name='createexpeditionlesson'),
    path("complete_lesson", views.complete_lesson, name='complete_lesson'),
    path("complete_lesson_exp", views.complete_lesson_exp, name='complete_lesson_exp'),
    path("make_exp_quiz", views.generate_quiz, name='generate_quiz'),
    path("complete_quiz_exp", views.after_quiz, name='after_quiz'),
    path("user/", views.fetch_user_info, name='user'),
    path("user/<str:username>", views.fetch_user_info, name='user'),
    path("exchange", views.mentorshipfeed, name='mentorshipfeed'),
    path("messages", views.messages, name='messages'),
]