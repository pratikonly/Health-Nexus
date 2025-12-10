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
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'core/home.html', {'profile': profile})

@login_required
def dashboard_home(request):
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
    return render(request, 'core/dashboard_home.html', context)

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
def analyze_food(request):
    if request.method == 'POST':
        try:
            import os
            import base64 as b64
            from google import genai
            from google.genai import types
            
            # Using Google Gemini API for food analysis
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                return JsonResponse({
                    'success': False, 
                    'error': 'Gemini API key not configured. Please add GEMINI_API_KEY in the Secrets tab.'
                })
            
            client = genai.Client(api_key=api_key)
            
            food_name = request.POST.get('food_name', '').strip()
            image_data = request.POST.get('image_data', '').strip()
            meal_type = request.POST.get('meal_type', 'snack')
            
            # Validate input
            if not image_data and not food_name:
                return JsonResponse({
                    'success': False, 
                    'error': 'Please provide either a food image or food name'
                })
            
            prompt = """Analyze this food and provide detailed nutrition information.
            Return ONLY a valid JSON object with this exact format (no markdown, no extra text):
            {
                "food_name": "name of the food",
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fats": 0,
                "fiber": 0,
                "serving_size": "estimated serving size",
                "health_tips": "brief health tip about this food"
            }
            Use realistic nutritional values based on a standard serving."""
            
            if image_data:
                # Extract base64 data and MIME type from data URL
                mime_type = "image/jpeg"  # default
                if ',' in image_data:
                    header, image_base64 = image_data.split(',', 1)
                    # Parse MIME type from header (e.g., "data:image/png;base64")
                    if 'image/png' in header:
                        mime_type = "image/png"
                    elif 'image/webp' in header:
                        mime_type = "image/webp"
                    elif 'image/gif' in header:
                        mime_type = "image/gif"
                else:
                    image_base64 = image_data
                
                image_bytes = b64.b64decode(image_base64)
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                        prompt,
                    ],
                )
            else:
                text_prompt = f"""Provide detailed nutrition information for: {food_name}
                Return ONLY a valid JSON object with this exact format (no markdown, no extra text):
                {{
                    "food_name": "{food_name}",
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fats": 0,
                    "fiber": 0,
                    "serving_size": "typical serving size",
                    "health_tips": "brief health tip about this food"
                }}
                Use realistic nutritional values based on a standard serving."""
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=text_prompt,
                )
            
            result_text = response.text if response.text else ""
            
            # Parse the response
            try:
                # Remove markdown code blocks if present
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                nutrition_data = json.loads(result_text.strip())
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Failed to parse nutrition data: {str(e)}'
                })
            
            # Save meal if requested
            save_meal = request.POST.get('save_meal', 'false') == 'true'
            if save_meal:
                meal = MealLog.objects.create(
                    user=request.user,
                    meal_type=meal_type,
                    food_name=nutrition_data.get('food_name', food_name),
                    calories=float(nutrition_data.get('calories', 0)),
                    protein=float(nutrition_data.get('protein', 0)),
                    carbs=float(nutrition_data.get('carbs', 0)),
                    fats=float(nutrition_data.get('fats', 0)),
                    fiber=float(nutrition_data.get('fiber', 0)),
                    serving_size=nutrition_data.get('serving_size', '1 serving')
                )
                
                # Save image if provided
                if image_data and ',' in image_data:
                    try:
                        format, imgstr = image_data.split(';base64,')
                        ext = format.split('/')[-1]
                        img_data = ContentFile(base64.b64decode(imgstr), name=f'food_{meal.id}.{ext}')
                        meal.food_image.save(f'food_{meal.id}.{ext}', img_data, save=True)
                    except Exception as img_error:
                        print(f"Image save error: {img_error}")
                
                nutrition_data['saved'] = True
                nutrition_data['meal_id'] = meal.id
            
            return JsonResponse({'success': True, 'data': nutrition_data})
            
        except Exception as e:
            import traceback
            print(f"Error in analyze_food: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False, 
                'error': f'An error occurred: {str(e)}'
            })
    
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
        try:
            # Update user information
            user = request.user
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.save()
            
            # Update profile gender
            gender = request.POST.get('gender', '').strip()
            if gender:
                profile.gender = gender
            
            # Update health metrics
            height = request.POST.get('height', '').strip()
            weight = request.POST.get('weight', '').strip()
            target_weight = request.POST.get('target_weight', '').strip()
            
            profile.height = float(height) if height else None
            profile.weight = float(weight) if weight else None
            profile.target_weight = float(target_weight) if target_weight else None
            
            # Update calorie goal
            calorie_goal = request.POST.get('daily_calorie_goal', '').strip()
            profile.daily_calorie_goal = int(calorie_goal) if calorie_goal else 2000
            
            # Update dietary preference
            dietary_pref = request.POST.get('dietary_preference', '').strip()
            profile.dietary_preference = dietary_pref if dietary_pref else 'none'
            
            # Update date of birth
            dob = request.POST.get('date_of_birth', '').strip()
            if dob:
                profile.date_of_birth = dob
            
            profile.save()
            
            messages.success(request, 'Settings updated successfully!')
        except ValueError as e:
            messages.error(request, 'Please enter valid numbers for height, weight, and calorie goal.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
        
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
