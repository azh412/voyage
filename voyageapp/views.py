from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.paginator import Paginator
import os, requests, random
from .models import *
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import openai
import random
import markdown
from spellchecker import SpellChecker
import re
import string
from datetime import datetime
from django.utils import timezone
import pytz

# Create a spell checker object
englishdictionary = SpellChecker()

openai.api_key = os.environ.get("OPENAI_API_KEY", "")

def index(request):
    return render(request, "index.html")
def register_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    if request.method == "POST":
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {"error": "Passwords do not match"})
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password):
            return render(request, "register.html", {"error": "Password needs at least eight characters, at least one letter, at least one number and at least one special character"})
        email = request.POST["email"]
        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        if len(username) > 50:
            return render(request, "register.html", {"error": "Username too long."})
        if len(first_name) > 50:
            return render(request, "register.html", {"error": "First name too long."})
        if len(last_name) > 50:
            return render(request, "register.html", {"error": "Last name too long."})
        if len(email) > 100:
            return render(request, "register.html", {"error": "Last name too long."})
        uuu = User.objects.filter(username=username)
        if len(uuu) != 0:
            return render(request, "register.html", {
                "error": "Username already taken."
            })
        uuu = User.objects.filter(email=email)
        if len(uuu) != 0:
            return render(request, "register.html", {
                "error": "Email already taken."
            })
        try:
            letters = string.ascii_uppercase
            code = ''.join(random.choice(letters) for i in range(3))
            user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name, account_created_at=timezone.now())
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "error": "Username already taken."
            })
        if user:
            login(request=request, user=user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "register.html")

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            user = User.objects.filter(email=username)
            user = user.first()
            if user:
                user = authenticate(username=user.username, password=password)
                if user:
                    login(request=request, user=user)
                    return HttpResponseRedirect(reverse("index"))
            return render(request, "login.html", {"error": "Invalid username and/or password"})
    return render(request, "login.html")
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))



@csrf_exempt
@login_required
def add_topics_to_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        load = data.get("interests")
        if len(load) < 4:
            return JsonResponse({"error": "You must provide 4 or more of your interests before moving on."})
        inst = [x.strip() for x in load if x != None]
        ins = []
        for i in inst:
            x = i.split(',')
            for xs in x:
                ins.append(xs.strip())
        topics = []
        request.user.interests.clear()
        request.user.save()
        # if len(englishdictionary.unknown(ins)) != 0:
        #     return JsonResponse({"error": "Invalid word(s)", "cleaned": englishdictionary.known(ins)})
        for i in ins:
            top = Topic(topic_name=i.lower(), userkey=request.user)
            top.save()
            request.user.interests.add(top)
            request.user.save()
        return JsonResponse({"message": str(request.user.interests.all().count())})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    

@csrf_exempt
@login_required
def save_likes(request):
    if request.method == "POST":
        data = json.loads(request.body)
        load = data.get("likes")
        inst = [x.strip() for x in load if x != None]
        ins = []
        for i in inst:
            x = i.split(',')
            for xs in x:
                ins.append(xs.strip())
        topics = []
        for i in ins:
            if i.lower() != 'random':
                if(len(Topic.objects.filter(topic_name=i.lower()).filter(userkey=request.user)) != 0):
                    # User.interests.filter(topic_name=i.lower())
                    x = Topic.objects.filter(topic_name=i.lower()).filter(userkey=request.user).first()
                    x.interest_factor += 1
                    x.save()
                else:
                    top = Topic(topic_name=i.lower(), userkey=request.user)
                    top.save()
                    request.user.interests.add(top)
                    request.user.save()
        return JsonResponse({"message": str(request.user.interests.all().count())})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    

@csrf_exempt
@login_required
def generate_titles_onboarding(request):
    if request.method == "GET":
        interests = request.user.interests.all()
        if interests.count() >= 23:
            request.user.onboarded = True
            request.user.save()
            return JsonResponse({"message":"onboarding complete"})
        else:
            user = []
            for t in interests:
                user.append(t.topic_name)
            while True:
                titles = []
                topics = []
                ingpt = [
                    {"role": "assistant", "content": """1. Introduction to Algebra / Arithmetic, Equations, Variables / math
            2. Understanding Newton's Laws of Motion / Physics, Forces, Motion / science
            3. Exploring the World of Genetics / DNA, Traits, Inheritance / science
            4. Mastering Calculus Techniques / Differentiation, Integration, Limits / math
            5. The Science of Exercise Physiology / Anatomy, Metabolism, Performance / sports
            6. The Art of Cooking / Recipes, Culinary Techniques, Ingredients / random"""},
                    {"role": "assistant", "content": """Recommended topics (raw):

1. Exploring the Laws of Thermodynamics / Energy, Heat, Entropy / science
2. The Science of Sports Performance / Physiology, Biomechanics, Nutrition / sports
3. Solving Complex Equations in Algebra / Quadratic, Exponential, Logarithmic Equations / math
4. Uncovering Ancient Civilizations / Archaeology, Culture, Artifacts / history
5. Geometry: The Study of Shapes and Patterns / Angles, Polygons, Congruence / math
6. The History of Fashion / Design, Trends, Clothing / random"""},
                    {"role": "system", "content": "Generate 6 lesson titles from comma-separated topics: 5 based on provided topics, and 1 random ones that isn't related to the provided topics. Include many related topics, broad and specific, inspired by titles. Also, include which topic you used to generate the title. Use a forward slash to separate titles from topics and another forward slash to separate topics from input topic(s). Exclude unnecessary characters. Example: 1. (TITLE) / (ALL POSSIBLE RELATED TOPICS) / (INPUT TOPIC)... 6. (RANDOM TITLE) / (ALL POSSIBLE RELATED TOPICS) / random"}
                ]
                chcs = []
                if interests.count() > 5:
                    for w in range(5):
                        chcs.append(random.choice(user))
                    chcs = list(set(chcs))
                    ingpt.append({"role": "user", "content": ",".join(chcs)})
                else:
                    ingpt.append({"role": "user", "content": ",".join(user)})

                itlt = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=ingpt,
                    user=str(request.user.id)
                )
                # print("Recommended topics (raw):")
                # print()
                # print(f"{itlt['choices'][0]['message']['content']}")
                # print()
                # print(f"Tokens used: {itlt['usage']['total_tokens']}")
                request.user.tokens_used += itlt['usage']['total_tokens']
                request.user.save()
                response = itlt['choices'][0]['message']['content']
                groups = response.split("\n")
                filteredgroups = []
                for i in groups:
                    if "/" in i:
                        if i.count("/") < 3:
                            filteredgroups.append(i)
                if len(filteredgroups) == 0:
                    continue
                for i in filteredgroups:
                    j = i.split("/")
                    titles.append(j[0].strip())
                    ts = j[1].strip()
                    ts += "," + j[2].strip()
                    topics.append(ts)
                break
            return JsonResponse({
                "topics": topics,
                "titles": titles
            })
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})
    
@csrf_exempt
@login_required
def generate_titles_onboarded(request):
    if request.method == "GET":
        ingpt2 = [
            {"role": "system", "content": "Given some topics / interests, create in total 3 possible lesson titles for possible lessons, not numbered"}
        ]
        interestsuser = request.user.interests.all()
        chosens = []
        for w in range(5):
            chosens.append(random.choice(interestsuser).topic_name)
        chosens = list(set(chosens))
        ingpt2.append({"role": "user", "content": ",".join(chosens)})
        itlt2 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=ingpt2,
                user=str(request.user.id)
                )
        response = itlt2['choices'][0]['message']['content']
        request.user.tokens_used += itlt2['usage']['total_tokens']
        request.user.save()
        titles = response.split("\n")
        return JsonResponse({"titles": titles, "topics": chosens})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})
    
@csrf_exempt
@login_required
def generate_lesson(request):
    if request.method == "POST":
        ingpt3 = [
            {"role": "system", "content": "Create a lesson in markdown format with an introduction header, conclusion header, and headers (max 8 words). Include 9 paragraphs. Add a separate '## QUESTIONS' paragraph with 5 common reader questions (Q: question) and their answers (A: answer). Headers start with ## in markdown, so all headers should begin with ##. Questions and answers are not headers."}
        ]
        data = json.loads(request.body)
        load = data.get("title")
        ingpt3.append({"role": "user", "content": load})
        ttl = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=ingpt3,
                user=str(request.user.id)
                )
        response = ttl['choices'][0]['message']['content']
        request.user.tokens_used += ttl['usage']['total_tokens']
        request.user.save()
        spl = response.split("## QUESTIONS")
        lesson = spl[0]
        qa = spl[1]
        qa = qa.split("\n\n")
        questions = []
        answers = []
        qa.pop(0)
        for i in qa:
            qas = i.split('A:')
            questions.append(qas[0].strip())
            answers.append(qas[1].strip())
        response = markdown.markdown(lesson)
        return JsonResponse({"lesson": response, "questions": questions, "answers": answers})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    

@csrf_exempt
@login_required
def feedback(request):
    if request.method == "POST":
        data = json.loads(request.body)
        load = data.get("topics")
        topics = [x.strip() for x in load if x != None]
        load = data.get("feedback")
        feedback = [x for x in load if x != None]
        d = 0
        for i in range(len(topics)):
            topic = topics[i]
            feedbackind = feedback[i]
            print(Topic.objects.filter(userkey=request.user))
            topicobj = Topic.objects.filter(userkey=request.user).filter(topic_name=topic).first()
            topicobj.interest_factor += feedbackind
            if topicobj.interest_factor >= 9.5:
                topicobj.interest_factor = 9.5
            elif topicobj.interest_factor <= 1:
                topicobj.delete()
                d += 1
            topicobj.save()
        return JsonResponse({"lesson": f"{d} interests cleared"})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    
@csrf_exempt
@login_required
def search(request):
    if request.method == "POST":
        ingpt3 = [
            {"role": "system", "content": "Create a lesson in markdown format with a lesson title header, introduction header, conclusion header, and headers (max 8 words), capable of teaching the user and answering and/or addressing the user's input. Include 10 paragraphs. Add a separate '## QUESTIONS' paragraph with 5 common reader questions (Q: question) and their answers (A: answer), separated by two new lines each. Headers start with ## in markdown, so all headers should begin with ##. Questions and answers are not headers. The lesson title header should not be the same as the user input. Include a header with links to good articles at the end for the reader to research further, titled '## FURTHER READING'. "}
        ]
        data = json.loads(request.body)
        load = data.get("query")
        query = load.strip()
        # if len(englishdictionary.unknown(query.split())) != 0:
        #     return JsonResponse({"error": "Invalid word(s)", "cleaned": englishdictionary.known(query.split())})
        ingpt3.append({"role": "user", "content": query})
        stl = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=ingpt3,
                user=str(request.user.id)
                )
        response = stl['choices'][0]['message']['content']
        request.user.tokens_used += stl['usage']['total_tokens']
        request.user.save()
        title = response.split('\n')[0]
        ingpt3 = [
            {"role": "system", "content": "Output two relevant one word keywords based on a lesson title with a comma as a delimiter."}
        ]
        ingpt3.append({"role": "user", "content": title})
        ttk = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=ingpt3,
                user=str(request.user.id)
                )
        keywords = ttk['choices'][0]['message']['content']
        request.user.tokens_used += ttk['usage']['total_tokens']
        request.user.save()
        for i in keywords.split(","):
            if(len(Topic.objects.filter(topic_name=i.lower()).filter(userkey=request.user)) != 0):
                x = Topic.objects.filter(topic_name=i.lower()).filter(userkey=request.user).first()
                x.interest_factor += 1
                x.save()
            else:
                top = Topic(topic_name=i.lower(), userkey=request.user)
                top.save()
                request.user.interests.add(top)
                request.user.save()
        spl = response.split("## QUESTIONS")
        lesson = spl[0]
        qa = spl[1]
        qa = qa.split("\n\n")
        questions = []
        answers = []
        qa.pop(0)
        for i in qa:
            if "A:" in i:
                qas = i.split('A:')
                questions.append(qas[0].strip())
                answers.append(qas[1].strip())
        response = markdown.markdown(lesson)
        return JsonResponse({"lesson": response, "questions": questions, "answers": answers})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})

def admin(request):
    return render(request, "admin.html")

def getusers(request):
    if request.method == "GET":
        users = []
        for user in User.objects.all():
            toadd = {}
            toadd['username'] = user.username
            toadd['email'] = user.email
            toadd['first_name'] = user.first_name
            toadd['last_name'] = user.last_name
            toadd['isAdmin'] = user.isAdmin
            toadd['tokens_used'] = user.tokens_used
            toadd['creation_date'] = user.account_created_at.date()
            toadd['onboarded'] = user.onboarded
            toadd['number_of_interests'] = user.interests.count()
            users.append(toadd)
        key = ['Username', 'Email', 'First Name', 'Last Name', 'Is Admin', 'Tokens Used', 'Account Creation Date', 'Onboarded', 'Number of Interests']
        return JsonResponse({"users": users, "key": key})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})
    
def expeditions(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            if request.user.expeditions.count() == 0:
                return HttpResponseRedirect(reverse("startexpedition"))
            else:
                return render(request, "expeditions.html", {"expeditions": request.user.expeditions.all()})
    else:
        return HttpResponseRedirect(reverse("login"))

def startexpedition(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            recommended_topics = []
            interests = Topic.objects.filter(userkey=request.user).all()
            top_interests = interests.order_by('-interest_factor')[:2]
            for i in top_interests:
                recommended_topics.append(i)
            least_interested = interests.order_by('interest_factor')[:2]
            for i in least_interested:
                recommended_topics.append(i)
            random_interests = interests.order_by('?')[:2]
            for i in random_interests:
                recommended_topics.append(i)
            random.shuffle(recommended_topics)
            return render(request, "startexpedition.html", {"recommended": recommended_topics})
    else:
        return HttpResponseRedirect(reverse("login"))

@csrf_exempt
@login_required
def complete_lesson(request):
    if request.method == "GET":
        request.user.lessons_completed += 1
        request.user.save()
        return JsonResponse({"message": request.user.lessons_completed})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})

@csrf_exempt
@login_required
def createexpedition(request):
    if request.method == "POST":
        data = json.loads(request.body)
        title = data.get("title")
        if len(title) > 90:
            return JsonResponse({"error": "Expedition name too long"})
        if len(request.user.expeditions.filter(expedition_name=title)) != 0:
            return JsonResponse({"error": "Expedition with that title already exists in your expeditions"})
        ingpt3 = [
            {"role": "system", "content": "given a desired skill to learn, generate chapters, at least 5, delimited by commas, needed to master, to master the skill, not numbered, no introductions or conclusion chapters."}
        ]
        ingpt3.append({"role": "user", "content": title})
        stl = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=ingpt3,
            user=str(request.user.id)
        )
        response = stl['choices'][0]['message']['content']
        request.user.tokens_used += stl['usage']['total_tokens']
        request.user.save()
        chapters = response.split(",")
        expedition = Expedition(expedition_name=title, userkey=request.user)
        expedition.save()
        for chap in chapters:
            chapter = Chapter(chapter_name=chap.strip(), userkey=request.user)
            chapter.save()
            expedition.chapters.add(chapter)
            expedition.save()
        request.user.expeditions.add(expedition)
        request.user.save()
        return JsonResponse({"message": expedition.expedition_name})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    
@csrf_exempt
@login_required
def createexpeditionlesson(request):
    if request.method == "POST":
        data = json.loads(request.body)
        load = data.get("expedition_name")
        expedition = Expedition.objects.filter(expedition_name=load).filter(userkey=request.user).first()
        if expedition is None:
            return JsonResponse({"error": "Expedition does not exist"})
        ingpt3 = [
            {"role": "system", "content": "Given a subtopic and topic, Create one of three lessons of the subtopic in markdown format with an introduction header, conclusion header, and headers (max 8 words). Include 11 paragraphs. Add a separate '## QUESTIONS' paragraph with 5 common reader questions (Q: question) and their answers (A: answer). Headers start with ## in markdown, so all headers should begin with ##. Questions and answers are not headers."}
        ]
        ingpt3.append({"role": "user", "content": f"Subtopic: {expedition.chapters.first().chapter_name} Topic: {expedition.expedition_name} Lesson #{(expedition.lessons_completed + 1) % 3}"})
        stl = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=ingpt3,
            user=str(request.user.id)
        )
        response = stl['choices'][0]['message']['content']
        print(response)
        request.user.tokens_used += stl['usage']['total_tokens']
        request.user.save()
        spl = response.split("## QUESTIONS")
        lesson = spl[0]
        qa = spl[1]
        qa = qa.split("\n\n")
        questions = []
        answers = []
        qa.pop(0)
        for i in qa:
            qas = i.split('A:')
            questions.append(qas[0].strip())
            answers.append(qas[1].strip())
        response = markdown.markdown(lesson)
        return JsonResponse({"lesson": response, "questions": questions, "answers": answers})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    
def getexpedition(request, expedition_id):
    if request.user.is_authenticated:
        if request.method == "GET":
            expedition = Expedition.objects.filter(id=expedition_id).first()
            if expedition is None:
                return HttpResponseRedirect(reverse("expeditions"))    
            chapters = expedition.chapters.all()
            total_chapters = chapters.count() + expedition.chapters_completed
            chapters_completed = expedition.chapters_completed
            percent_completed = (chapters_completed / total_chapters) * 100
            return render(request, "expedition.html", {
                "expedition": expedition, 
                "chapters": chapters, 
                "total_chapters": total_chapters, 
                "chapters_completed": chapters_completed, 
                "percent_completed": round(percent_completed, 3),
                "current_chapter": chapters[0],
                "curr_lesson": expedition.lessons_completed + 1
            })
    else:
        return HttpResponseRedirect(reverse("login"))

@csrf_exempt
@login_required
def complete_lesson_exp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        load = data.get("expedition_name")
        expedition = Expedition.objects.filter(expedition_name=load).filter(userkey=request.user).first()
        if expedition is None:
            return JsonResponse({"error": "Expedition does not exist"})
        expedition.lessons_completed += 1
        expedition.save()
        return JsonResponse({"message": expedition.lessons_completed})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected GET"})
    
@csrf_exempt
@login_required
def generate_quiz(request):
    if request.method == "POST":
        data = json.loads(request.body)
        skill = data.get("expedition_name")
        subskill = data.get("chapter_name")
        ingpt3 = [
            {"role": "system", "content": 'Generate a multiple-choice quiz consisting of 6 questions to evaluate the knowledge level of the person answering based on a subskill and skill. Questions are not numbered and start with "Q:", answer choices start with ".". Correct answers start with ".*". DO NOT INCLUDE UNNECCESARY CHARACTERS.'},
            {"role": "assistant", "content": """Q: What is the purpose of grappling in MMA?
. To immobilize and control the opponent
. To strike the opponent with punches and kicks
. To avoid being taken down by the opponent
. To win the match by knockout or submission
.* To gain an advantage in close-range combat and potentially submit the opponent.

Q: What is a rear-naked choke?
. A punch targeted at the opponent's face
. A leg lock submission technique
. A takedown technique used to bring the opponent to the ground
.* A submission hold that involves wrapping the arms around the opponent's neck and cutting off blood circulation to the brain.

Q: What is a guillotine choke?
.* A submission hold that targets the opponent's neck using the arms
. A takedown technique used to bring the opponent to the ground
. A leg lock submission technique
. A strike targeted at the opponent's groin area

Q: What is side control in MMA grappling?
. A technique used to sweep the opponent from the bottom position
.* A dominant top position where the person applying it is sideways to the opponent, pinning their body to the ground
. A submission hold that involves bending the opponent's leg in an unnatural direction
. A strike targeted at the opponent's kidneys

Q: What is the purpose of the guard position in MMA grappling?
. To avoid punches and strikes from the opponent
.* To control the opponent and potentially set up submission opportunities
. To prevent the opponent from taking the back
. To escape from the bottom position

Q: What is a double-leg takedown?
. A submission hold that targets the opponent's arm joint
. A strike targeted at the opponent's nose
.* A technique where the person applying it shoots in and drives through the opponent's legs, lifting them up and taking them down to the ground
. A position where the person applying it has both legs wrapped around the opponent's body"""}
        ]
        ingpt3.append({"role": "user", "content": f"Subskill: {subskill} Skill: {skill}"})
        stl = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=ingpt3,
            user=str(request.user.id)
        )
        response = stl['choices'][0]['message']['content']
        print(response)
        request.user.tokens_used += stl['usage']['total_tokens']
        request.user.save()
        spl = response.split("Q:")
        questions = []
        answers = []
        correct_answers = []
        for i in spl:
            qas = i.split('.')
            x = []
            for j in range(len(qas)):
                if j == 0:
                    questions.append(qas[j].strip())
                else:
                    print(qas[j])
                    if len(qas[j]) > 2 and qas[j][0] == '*':
                        correct_answers.append(qas[j][1:].strip())
                    else:
                        x.append(qas[j].strip())
            answers.append(x)
        return JsonResponse({"questions": questions[1:], "answers": answers[1:], "correct_answers": correct_answers})
    else:
        return JsonResponse({"error": "Unexpected request type. Expected POST"})
    
@csrf_exempt
@login_required
def after_quiz(request):
    if request.method == "POST":
        data = json.loads(request.body)
        skill = data.get("expedition_name")
        score = data.get("score")
        expedition = Expedition.objects.filter(expedition_name=skill).filter(userkey=request.user).first()
        if expedition is None:
            return JsonResponse({"error": "Expedition does not exist"})
        score_to_percent = round(score * 100, 2)
        if score_to_percent >= 80:
            expedition.chapters_completed += 1
            expedition.lessons_completed = 0
            expedition.save()
            if expedition.chapters.count() > 0:
                expedition.chapters.remove(expedition.chapters.first())
                expedition.save()
            else:
                expedition.delete()
                return HttpResponseRedirect(reverse("expeditions"))
            return JsonResponse({"message": f"You passed! You have completed this chapter! Your score was {score_to_percent}%. On to the next chapter!"})
        else:
            return JsonResponse({"message": f"Unfortunately, you did not pass this time. But don't worry, you're making progress! You got {score_to_percent}% correct. Keep practicing and you'll get there. You can do it!"})
        

def fetch_user_info(request, username=None):
    if username == None:
        if request.user.is_authenticated:
            if request.method == "GET":
                user = request.user.interests.all().order_by('-interest_factor')[:13]
                interest_to_factor = []
                sum = 0
                for i in user:
                    x = [i.topic_name, i.interest_factor]
                    print(x)
                    sum += i.interest_factor
                    interest_to_factor.append(x)
                sum = sum / len(interest_to_factor)
                for i in interest_to_factor:
                    i[1] = round((i[1] / sum) * 2, 2)
                interest_to_factor = sorted(interest_to_factor, key=lambda x: x[1], reverse=True)
                return render(request, "user.html", {"user": request.user, "interests": interest_to_factor, "sum": sum})
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        if request.method == "GET":
            userg = User.objects.filter(username=username).first()
            if userg is None:
                return HttpResponseRedirect(reverse("user"))
            user = userg.interests.all().order_by('-interest_factor')[:13]
            interest_to_factor = []
            sum = 0
            for i in user:
                x = [i.topic_name, i.interest_factor]
                print(x)
                sum += i.interest_factor
                interest_to_factor.append(x)
            sum = sum / len(interest_to_factor)
            for i in interest_to_factor:
                i[1] = round((i[1] / sum) * 2, 2)
            interest_to_factor = sorted(interest_to_factor, key=lambda x: x[1], reverse=True)
            return render(request, "user.html", {"user": userg, "interests": interest_to_factor, "sum": sum})

def mentorshipfeed(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            posts = MentorshipPost.objects.all().order_by('created_at')
            x = []
            for i in posts:
                x.append((i.userkey.interests.all().order_by('-interest_factor').first().topic_name, i))
            return render(request, "mentorshipfeed.html", {
                "posts": posts,
                "x": x
            })
        if request.method == 'POST':
            post = request.POST["post"]
            posts = MentorshipPost.objects.all().order_by('created_at')
            x = []
            for i in posts:
                x.append((i.userkey.interests.all().order_by('-interest_factor').first().topic_name, i))
            if len(post) >= 150:
                return render(request, "mentorshipfeed.html", {
                    "error": "Post too long. Must be less than 150 characters.",
                    "post": post,
                    "x": x
                })
        ingpt3 = [
            {"role": "system", "content": "given a post, decide whether the post is appropriate and talks about the user's experience and what they will teach. reply with y or n, and if not appropriate, say na"}
        ]
        ingpt3.append({"role": "user", "content": f"{post}"})
        stl = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=ingpt3,
            user=str(request.user.id)
        )
        response = stl['choices'][0]['message']['content']
        print(response)
        request.user.tokens_used += stl['usage']['total_tokens']
        request.user.save()
        if response == "na":
            posts = MentorshipPost.objects.all().order_by('created_at')
            x = []
            for i in posts:
                x.append((i.userkey.interests.all().order_by('-interest_factor').first().topic_name, i))
            return render(request, "mentorshipfeed.html", {
                "error": "Post not appropriate. Please try again.",
                "post": post,
                "x": x
            })
        elif response == "n":
            posts = MentorshipPost.objects.all().order_by('created_at')
            x = []
            for i in posts:
                x.append((i.userkey.interests.all().order_by('-interest_factor').first().topic_name, i))
            return render(request, "mentorshipfeed.html", {
                "error": "Please add more information to your post.",
                "post": post,
                "x": x,
            })
        else:
            dpost = MentorshipPost(post=post, userkey=request.user)
            dpost.save()
            return HttpResponseRedirect(reverse("mentorshipfeed"))
    else:
        return HttpResponseRedirect(reverse("login"))
    
def messages(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            return render(request, "messages.html")
    else:
        return HttpResponseRedirect(reverse("login"))