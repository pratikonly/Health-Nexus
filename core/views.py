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
            import requests

            food_name = request.POST.get('food_name', '').strip()
            image_data = request.POST.get('image_data', '').strip()
            meal_type = request.POST.get('meal_type', 'snack')

            # If image is provided, detect food from image using Clarifai
            if image_data and not food_name:
                try:
                    # Use Clarifai Food Recognition API
                    clarifai_api_key = os.environ.get('CLARIFAI_API_KEY', '')

                    if clarifai_api_key:
                        # Convert base64 to clean format
                        if ',' in image_data:
                            image_data_clean = image_data.split(',')[1]
                        else:
                            image_data_clean = image_data

                        clarifai_url = 'https://api.clarifai.com/v2/models/food-item-recognition/outputs'
                        headers = {
                            'Authorization': f'Key {clarifai_api_key}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            'inputs': [{
                                'data': {
                                    'image': {
                                        'base64': image_data_clean
                                    }
                                }
                            }]
                        }

                        recognition_response = requests.post(clarifai_url, json=payload, headers=headers, timeout=10)

                        if recognition_response.status_code == 200:
                            recognition_data = recognition_response.json()
                            # Extract detected food name from Clarifai response
                            if 'outputs' in recognition_data and len(recognition_data['outputs']) > 0:
                                concepts = recognition_data['outputs'][0].get('data', {}).get('concepts', [])
                                if concepts and len(concepts) > 0:
                                    food_name = concepts[0].get('name', '')

                    # If still no food name, ask user to enter manually
                    if not food_name:
                        return JsonResponse({
                            'success': False,
                            'error': 'Could not detect food from image. Please enter the food name manually or add CLARIFAI_API_KEY to Secrets.'
                        })

                except Exception as e:
                    print(f"Food recognition error: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Could not detect food from image. Please enter the food name manually.'
                    })

            # Validate input - food name is required for nutrition lookup
            if not food_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Please upload an image or enter the food name'
                })

            # Use Edamam Food Database API for nutrition data
            edamam_app_id = os.environ.get('EDAMAM_APP_ID', '')
            edamam_app_key = os.environ.get('EDAMAM_APP_KEY', '')

            if edamam_app_id and edamam_app_key:
                # Use Edamam Nutrition Analysis API
                edamam_url = 'https://api.edamam.com/api/nutrition-details'
                params = {
                    'app_id': edamam_app_id,
                    'app_key': edamam_app_key
                }
                payload = {
                    'title': food_name,
                    'ingr': [f'1 serving of {food_name}']
                }

                response = requests.post(edamam_url, params=params, json=payload, timeout=10)

                if response.status_code == 200:
                    api_data = response.json()

                    total_nutrients = api_data.get('totalNutrients', {})

                    nutrition_data = {
                        'food_name': food_name.title(),
                        'calories': round(api_data.get('calories', 0), 1),
                        'protein': round(total_nutrients.get('PROCNT', {}).get('quantity', 0), 1),
                        'carbs': round(total_nutrients.get('CHOCDF', {}).get('quantity', 0), 1),
                        'fats': round(total_nutrients.get('FAT', {}).get('quantity', 0), 1),
                        'fiber': round(total_nutrients.get('FIBTG', {}).get('quantity', 0), 1),
                        'serving_size': '1 serving',
                        'health_tips': f'This meal contains {round(total_nutrients.get("SUGAR", {}).get("quantity", 0), 1)}g of sugar.'
                    }
                else:
                    # Fallback to API Ninjas
                    api_url = f'https://api.api-ninjas.com/v1/nutrition?query={food_name}'
                    api_key = os.environ.get('NUTRITION_API_KEY', '')

                    headers = {'X-Api-Key': api_key} if api_key else {}
                    response = requests.get(api_url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        api_data = response.json()
                        if api_data and len(api_data) > 0:
                            item = api_data[0]
                            nutrition_data = {
                                'food_name': item.get('name', food_name).title(),
                                'calories': round(item.get('calories', 0), 1),
                                'protein': round(item.get('protein_g', 0), 1),
                                'carbs': round(item.get('carbohydrates_total_g', 0), 1),
                                'fats': round(item.get('fat_total_g', 0), 1),
                                'fiber': round(item.get('fiber_g', 0), 1),
                                'serving_size': f"{item.get('serving_size_g', 100)}g",
                                'health_tips': f'Contains {round(item.get("sugar_g", 0), 1)}g of sugar.'
                            }
                        else:
                            raise Exception('No data')
                    else:
                        raise Exception('API error')
            else:
                # Fallback to API Ninjas if Edamam not configured
                api_url = f'https://api.api-ninjas.com/v1/nutrition?query={food_name}'
                api_key = os.environ.get('NUTRITION_API_KEY', '')

                headers = {'X-Api-Key': api_key} if api_key else {}
                response = requests.get(api_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    api_data = response.json()
                    if api_data and len(api_data) > 0:
                        item = api_data[0]
                        nutrition_data = {
                            'food_name': item.get('name', food_name).title(),
                            'calories': round(item.get('calories', 0), 1),
                            'protein': round(item.get('protein_g', 0), 1),
                            'carbs': round(item.get('carbohydrates_total_g', 0), 1),
                            'fats': round(item.get('fat_total_g', 0), 1),
                            'fiber': round(item.get('fiber_g', 0), 1),
                            'serving_size': f"{item.get('serving_size_g', 100)}g",
                            'health_tips': f'Contains {round(item.get("sugar_g", 0), 1)}g of sugar.'
                        }
                    else:
                        raise Exception('No data')
                else:
                    raise Exception('API error')

        except Exception as e:
            # Final fallback with estimated values
            print(f"Nutrition API error: {str(e)}")
            nutrition_data = {
                'food_name': food_name.title() if food_name else 'Unknown Food',
                'calories': 150,
                'protein': 5,
                'carbs': 20,
                'fats': 5,
                'fiber': 2,
                'serving_size': '1 serving',
                'health_tips': 'Nutrition data unavailable. Values shown are estimates. Consider adding API keys to Secrets.'
            }

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

        else: # This else belongs to the initial `if edamam_app_id and edamam_app_key:` block
            # Fallback to API Ninjas if Edamam not configured
            api_url = f'https://api.api-ninjas.com/v1/nutrition?query={food_name}'
            api_key = os.environ.get('NUTRITION_API_KEY', '')

            headers = {'X-Api-Key': api_key} if api_key else {}
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                api_data = response.json()
                if api_data and len(api_data) > 0:
                    item = api_data[0]
                    nutrition_data = {
                        'food_name': item.get('name', food_name).title(),
                        'calories': round(item.get('calories', 0), 1),
                        'protein': round(item.get('protein_g', 0), 1),
                        'carbs': round(item.get('carbohydrates_total_g', 0), 1),
                        'fats': round(item.get('fat_total_g', 0), 1),
                        'fiber': round(item.get('fiber_g', 0), 1),
                        'serving_size': f"{item.get('serving_size_g', 100)}g",
                        'health_tips': f'Contains {round(item.get("sugar_g", 0), 1)}g of sugar.'
                    }
                else:
                    raise Exception('No data')
            else:
                raise Exception('API error')

        # This part is outside the `try...except` block for `Exception as e`
        # It handles the successful retrieval of nutrition_data and saving the meal.
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