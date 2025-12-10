import json
import base64
import os
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .models import MealLog, WeightLog, DietPlan, Quiz, QuizQuestion, QuizResult, HealthQuote
from accounts.models import UserProfile

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')

@login_required
def dashboard(request):
    return redirect('home')

@login_required
def home(request):
    today = datetime.now().date()
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    today_meals = MealLog.objects.filter(user=request.user, date=today)
    today_calories = today_meals.aggregate(total=Sum('calories'))['total'] or 0
    today_protein = today_meals.aggregate(total=Sum('protein'))['total'] or 0
    today_carbs = today_meals.aggregate(total=Sum('carbs'))['total'] or 0
    today_fats = today_meals.aggregate(total=Sum('fats'))['total'] or 0
    
    quotes = [
        {"quote": "Take care of your body. It's the only place you have to live.", "author": "Jim Rohn"},
        {"quote": "The groundwork for all happiness is good health.", "author": "Leigh Hunt"},
        {"quote": "Health is not about the weight you lose, but about the life you gain.", "author": "Josh Axe"},
        {"quote": "Your body hears everything your mind says.", "author": "Naomi Judd"},
        {"quote": "A healthy outside starts from the inside.", "author": "Robert Urich"},
    ]
    import random
    quote = random.choice(quotes)
    
    quiz_count = QuizResult.objects.filter(user=request.user).count()
    meals_logged = MealLog.objects.filter(user=request.user).count()
    
    context = {
        'profile': profile,
        'today_calories': round(today_calories, 1),
        'today_protein': round(today_protein, 1),
        'today_carbs': round(today_carbs, 1),
        'today_fats': round(today_fats, 1),
        'calorie_goal': profile.daily_calorie_goal,
        'calorie_percentage': min(100, round((today_calories / profile.daily_calorie_goal) * 100)) if profile.daily_calorie_goal > 0 else 0,
        'quote': quote,
        'quiz_count': quiz_count,
        'meals_logged': meals_logged,
    }
    return render(request, 'core/home.html', context)

@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()
    user_results = QuizResult.objects.filter(user=request.user)
    
    quiz_data = []
    for quiz in quizzes:
        result = user_results.filter(quiz=quiz).first()
        quiz_data.append({
            'quiz': quiz,
            'result': result,
            'question_count': quiz.questions.count()
        })
    
    return render(request, 'core/quiz_list.html', {'quiz_data': quiz_data})

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    return render(request, 'core/quiz_detail.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_submit(request, quiz_id):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = quiz.questions.all()
        
        correct = 0
        total = questions.count()
        
        for question in questions:
            answer = request.POST.get(f'question_{question.id}')
            if answer and answer.lower() == question.correct_answer.lower():
                correct += 1
        
        percentage = (correct / total * 100) if total > 0 else 0
        
        QuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=correct,
            total_questions=total,
            percentage=percentage
        )
        
        messages.success(request, f'Quiz completed! You scored {correct}/{total} ({percentage:.1f}%)')
        return redirect('quiz_list')
    
    return redirect('quiz_list')

@login_required
def progress(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    weight_logs = WeightLog.objects.filter(user=request.user).order_by('date')[:30]
    
    last_7_days = []
    today = datetime.now().date()
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        meals = MealLog.objects.filter(user=request.user, date=date)
        calories = meals.aggregate(total=Sum('calories'))['total'] or 0
        last_7_days.append({
            'date': date.strftime('%a'),
            'calories': round(calories, 1)
        })
    
    quiz_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')[:10]
    
    context = {
        'profile': profile,
        'weight_logs': weight_logs,
        'last_7_days': last_7_days,
        'quiz_results': quiz_results,
    }
    return render(request, 'core/progress.html', context)

@login_required
def ai_cam(request):
    recent_analyses = MealLog.objects.filter(user=request.user, food_image__isnull=False).order_by('-logged_at')[:5]
    return render(request, 'core/ai_cam.html', {'recent_analyses': recent_analyses})

@login_required
@csrf_exempt
def analyze_food(request):
    if request.method == 'POST':
        try:
            from openai import OpenAI
            
            client = OpenAI()
            
            food_name = request.POST.get('food_name', '')
            image_data = request.POST.get('image_data', '')
            meal_type = request.POST.get('meal_type', 'snack')
            
            if image_data:
                prompt = f"""Analyze this food image and provide detailed nutrition information.
                Return ONLY a JSON object with this exact format:
                {{
                    "food_name": "name of the food",
                    "calories": number,
                    "protein": number in grams,
                    "carbs": number in grams,
                    "fats": number in grams,
                    "fiber": number in grams,
                    "serving_size": "estimated serving size",
                    "health_tips": "brief health tip about this food"
                }}"""
                
                image_content = image_data.split(',')[1] if ',' in image_data else image_data
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_data}}
                            ]
                        }
                    ],
                    max_tokens=500
                )
            else:
                prompt = f"""Provide detailed nutrition information for: {food_name}
                Return ONLY a JSON object with this exact format:
                {{
                    "food_name": "{food_name}",
                    "calories": number,
                    "protein": number in grams,
                    "carbs": number in grams,
                    "fats": number in grams,
                    "fiber": number in grams,
                    "serving_size": "typical serving size",
                    "health_tips": "brief health tip about this food"
                }}"""
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
            
            result_text = response.choices[0].message.content
            
            try:
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                nutrition_data = json.loads(result_text.strip())
            except json.JSONDecodeError:
                nutrition_data = {
                    "food_name": food_name or "Unknown Food",
                    "calories": 150,
                    "protein": 5,
                    "carbs": 20,
                    "fats": 5,
                    "fiber": 2,
                    "serving_size": "1 serving",
                    "health_tips": "Unable to analyze. Please try again."
                }
            
            save_meal = request.POST.get('save_meal', 'false') == 'true'
            if save_meal:
                meal = MealLog.objects.create(
                    user=request.user,
                    meal_type=meal_type,
                    food_name=nutrition_data.get('food_name', food_name),
                    calories=nutrition_data.get('calories', 0),
                    protein=nutrition_data.get('protein', 0),
                    carbs=nutrition_data.get('carbs', 0),
                    fats=nutrition_data.get('fats', 0),
                    fiber=nutrition_data.get('fiber', 0),
                    serving_size=nutrition_data.get('serving_size', '1 serving')
                )
                
                if image_data and ',' in image_data:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    img_data = ContentFile(base64.b64decode(imgstr), name=f'food_{meal.id}.{ext}')
                    meal.food_image.save(f'food_{meal.id}.{ext}', img_data, save=True)
                
                nutrition_data['saved'] = True
                nutrition_data['meal_id'] = meal.id
            
            return JsonResponse({'success': True, 'data': nutrition_data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def diet_plan(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    today = datetime.now().date()
    today_meals = MealLog.objects.filter(user=request.user, date=today).order_by('logged_at')
    
    today_totals = today_meals.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbs'),
        fats=Sum('fats')
    )
    
    last_7_days = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        meals = MealLog.objects.filter(user=request.user, date=date)
        totals = meals.aggregate(
            calories=Sum('calories'),
            protein=Sum('protein'),
            carbs=Sum('carbs'),
            fats=Sum('fats')
        )
        last_7_days.append({
            'date': date,
            'day': date.strftime('%a'),
            'calories': round(totals['calories'] or 0, 1),
            'protein': round(totals['protein'] or 0, 1),
            'carbs': round(totals['carbs'] or 0, 1),
            'fats': round(totals['fats'] or 0, 1),
        })
    
    context = {
        'profile': profile,
        'today_meals': today_meals,
        'today_totals': {
            'calories': round(today_totals['calories'] or 0, 1),
            'protein': round(today_totals['protein'] or 0, 1),
            'carbs': round(today_totals['carbs'] or 0, 1),
            'fats': round(today_totals['fats'] or 0, 1),
        },
        'last_7_days': last_7_days,
    }
    return render(request, 'core/diet_plan.html', context)

@login_required
def log_meal(request):
    if request.method == 'POST':
        MealLog.objects.create(
            user=request.user,
            meal_type=request.POST.get('meal_type', 'snack'),
            food_name=request.POST.get('food_name'),
            calories=float(request.POST.get('calories', 0)),
            protein=float(request.POST.get('protein', 0)),
            carbs=float(request.POST.get('carbs', 0)),
            fats=float(request.POST.get('fats', 0)),
            fiber=float(request.POST.get('fiber', 0)),
            serving_size=request.POST.get('serving_size', '1 serving'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Meal logged successfully!')
    return redirect('diet_plan')

@login_required
def delete_meal(request, meal_id):
    meal = get_object_or_404(MealLog, id=meal_id, user=request.user)
    meal.delete()
    messages.success(request, 'Meal deleted successfully!')
    return redirect('diet_plan')

@login_required
def settings_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        profile.height = float(request.POST.get('height', 0)) or None
        profile.weight = float(request.POST.get('weight', 0)) or None
        profile.target_weight = float(request.POST.get('target_weight', 0)) or None
        profile.daily_calorie_goal = int(request.POST.get('daily_calorie_goal', 2000))
        profile.dietary_preference = request.POST.get('dietary_preference', 'none')
        
        dob = request.POST.get('date_of_birth')
        if dob:
            profile.date_of_birth = dob
        
        profile.save()
        
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')
    
    return render(request, 'core/settings.html', {'profile': profile})

@login_required
def log_weight(request):
    if request.method == 'POST':
        weight = float(request.POST.get('weight', 0))
        date_str = request.POST.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = datetime.now().date()
        
        WeightLog.objects.update_or_create(
            user=request.user,
            date=date,
            defaults={'weight': weight}
        )
        
        profile = request.user.profile
        profile.weight = weight
        profile.save()
        
        messages.success(request, 'Weight logged successfully!')
    
    return redirect('progress')

@login_required
def get_nutrition_data(request):
    today = datetime.now().date()
    meals = MealLog.objects.filter(user=request.user, date=today)
    
    totals = meals.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbs'),
        fats=Sum('fats')
    )
    
    return JsonResponse({
        'calories': round(totals['calories'] or 0, 1),
        'protein': round(totals['protein'] or 0, 1),
        'carbs': round(totals['carbs'] or 0, 1),
        'fats': round(totals['fats'] or 0, 1),
    })

@login_required
def get_progress_data(request):
    today = datetime.now().date()
    data = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        meals = MealLog.objects.filter(user=request.user, date=date)
        calories = meals.aggregate(total=Sum('calories'))['total'] or 0
        data.append({
            'date': date.strftime('%a'),
            'calories': round(calories, 1)
        })
    
    return JsonResponse({'data': data})
