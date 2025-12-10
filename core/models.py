from django.db import models
from django.contrib.auth.models import User

class MealLog(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_logs')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    food_name = models.CharField(max_length=200)
    food_image = models.ImageField(upload_to='food_images/', null=True, blank=True)
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0, help_text="Protein in grams")
    carbs = models.FloatField(default=0, help_text="Carbohydrates in grams")
    fats = models.FloatField(default=0, help_text="Fats in grams")
    fiber = models.FloatField(default=0, help_text="Fiber in grams")
    serving_size = models.CharField(max_length=100, default="1 serving")
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.food_name} - {self.user.username}"

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    weight = models.FloatField(help_text="Weight in kg")
    date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.date}"

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_calories = models.IntegerField()
    target_protein = models.FloatField(default=0)
    target_carbs = models.FloatField(default=0)
    target_fats = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('nutrition', 'Nutrition'),
        ('fitness', 'Fitness'),
        ('wellness', 'Wellness'),
        ('mental_health', 'Mental Health'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[
        ('a', 'Option A'),
        ('b', 'Option B'),
        ('c', 'Option C'),
        ('d', 'Option D'),
    ])
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quiz.title} - Q{self.id}"

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}: {self.percentage}%"

class HealthQuote(models.Model):
    quote = models.TextField()
    author = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=[
        ('motivation', 'Motivation'),
        ('nutrition', 'Nutrition'),
        ('fitness', 'Fitness'),
        ('wellness', 'Wellness'),
    ])

    def __str__(self):
        return f'"{self.quote[:50]}..." - {self.author}'
