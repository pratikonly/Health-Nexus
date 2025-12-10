from django.core.management.base import BaseCommand
from core.models import Quiz, QuizQuestion

class Command(BaseCommand):
    help = 'Seed the database with sample quizzes'

    def handle(self, *args, **options):
        nutrition_quiz, created = Quiz.objects.get_or_create(
            title="Nutrition Basics",
            defaults={
                'description': "Test your knowledge about essential nutrients and healthy eating habits.",
                'category': 'nutrition'
            }
        )
        
        if created:
            QuizQuestion.objects.create(
                quiz=nutrition_quiz,
                question_text="Which vitamin is primarily obtained from sunlight exposure?",
                option_a="Vitamin A",
                option_b="Vitamin B12",
                option_c="Vitamin C",
                option_d="Vitamin D",
                correct_answer="d",
                explanation="Vitamin D is synthesized in the skin when exposed to sunlight."
            )
            QuizQuestion.objects.create(
                quiz=nutrition_quiz,
                question_text="Which macronutrient provides the most calories per gram?",
                option_a="Carbohydrates",
                option_b="Proteins",
                option_c="Fats",
                option_d="Fiber",
                correct_answer="c",
                explanation="Fats provide 9 calories per gram, while carbs and proteins provide 4 calories per gram."
            )
            QuizQuestion.objects.create(
                quiz=nutrition_quiz,
                question_text="What is the recommended daily water intake for an average adult?",
                option_a="4 glasses",
                option_b="6 glasses",
                option_c="8 glasses",
                option_d="12 glasses",
                correct_answer="c",
                explanation="8 glasses (about 2 liters) of water per day is commonly recommended."
            )
            QuizQuestion.objects.create(
                quiz=nutrition_quiz,
                question_text="Which food is the best source of omega-3 fatty acids?",
                option_a="Chicken breast",
                option_b="Salmon",
                option_c="White rice",
                option_d="Potatoes",
                correct_answer="b",
                explanation="Fatty fish like salmon are excellent sources of omega-3 fatty acids."
            )
            QuizQuestion.objects.create(
                quiz=nutrition_quiz,
                question_text="What nutrient helps build and repair muscle tissue?",
                option_a="Carbohydrates",
                option_b="Fiber",
                option_c="Protein",
                option_d="Vitamin C",
                correct_answer="c",
                explanation="Protein is essential for building and repairing muscle tissue."
            )

        fitness_quiz, created = Quiz.objects.get_or_create(
            title="Fitness Fundamentals",
            defaults={
                'description': "How much do you know about exercise and physical fitness?",
                'category': 'fitness'
            }
        )
        
        if created:
            QuizQuestion.objects.create(
                quiz=fitness_quiz,
                question_text="How many minutes of moderate exercise per week do health experts recommend?",
                option_a="75 minutes",
                option_b="150 minutes",
                option_c="300 minutes",
                option_d="60 minutes",
                correct_answer="b",
                explanation="The WHO recommends at least 150 minutes of moderate-intensity exercise per week."
            )
            QuizQuestion.objects.create(
                quiz=fitness_quiz,
                question_text="Which type of exercise is best for improving cardiovascular health?",
                option_a="Weight lifting",
                option_b="Stretching",
                option_c="Aerobic exercise",
                option_d="Balance training",
                correct_answer="c",
                explanation="Aerobic exercises like running, swimming, and cycling improve cardiovascular health."
            )
            QuizQuestion.objects.create(
                quiz=fitness_quiz,
                question_text="What should you do before starting an exercise routine?",
                option_a="Eat a large meal",
                option_b="Warm up",
                option_c="Drink energy drinks",
                option_d="Skip stretching",
                correct_answer="b",
                explanation="Warming up prepares your body for exercise and helps prevent injuries."
            )
            QuizQuestion.objects.create(
                quiz=fitness_quiz,
                question_text="How long should you rest between strength training sessions for the same muscle group?",
                option_a="12 hours",
                option_b="24 hours",
                option_c="48 hours",
                option_d="1 week",
                correct_answer="c",
                explanation="Muscles need about 48 hours to recover and rebuild after strength training."
            )

        wellness_quiz, created = Quiz.objects.get_or_create(
            title="Wellness & Mental Health",
            defaults={
                'description': "Explore your understanding of holistic wellness and mental health.",
                'category': 'wellness'
            }
        )
        
        if created:
            QuizQuestion.objects.create(
                quiz=wellness_quiz,
                question_text="How many hours of sleep do most adults need per night?",
                option_a="4-5 hours",
                option_b="5-6 hours",
                option_c="7-9 hours",
                option_d="10-12 hours",
                correct_answer="c",
                explanation="Most adults need 7-9 hours of quality sleep for optimal health."
            )
            QuizQuestion.objects.create(
                quiz=wellness_quiz,
                question_text="Which activity is known to reduce stress and improve mental clarity?",
                option_a="Watching TV for hours",
                option_b="Meditation",
                option_c="Skipping meals",
                option_d="Working overtime",
                correct_answer="b",
                explanation="Meditation has been proven to reduce stress and improve mental clarity."
            )
            QuizQuestion.objects.create(
                quiz=wellness_quiz,
                question_text="What is a common sign of dehydration?",
                option_a="Increased energy",
                option_b="Clear urine",
                option_c="Headache and fatigue",
                option_d="Improved focus",
                correct_answer="c",
                explanation="Headaches and fatigue are common signs of dehydration."
            )
            QuizQuestion.objects.create(
                quiz=wellness_quiz,
                question_text="Which practice helps maintain a healthy work-life balance?",
                option_a="Always being available for work",
                option_b="Setting boundaries and taking breaks",
                option_c="Skipping vacations",
                option_d="Checking emails before bed",
                correct_answer="b",
                explanation="Setting boundaries and taking regular breaks helps maintain work-life balance."
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded quizzes!'))
