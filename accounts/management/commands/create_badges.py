# accounts/management/commands/create_badges.py
from django.core.management.base import BaseCommand
from accounts.models import Badge

class Command(BaseCommand):
    help = 'Creates sample badges'

    def handle(self, *args, **kwargs):
        badges = [
            {
                'name': 'Beginner',
                'description': 'Welcome to EduVolve! You\'ve earned your first points.',
                'icon': 'star',
                'points_required': 0,
                'color': 'secondary'
            },
            {
                'name': 'Quick Learner',
                'description': 'Earned 100 points',
                'icon': 'lightning',
                'points_required': 100,
                'color': 'primary'
            },
            {
                'name': 'Dedicated Student',
                'description': 'Earned 500 points',
                'icon': 'book',
                'points_required': 500,
                'color': 'info'
            },
            {
                'name': 'Rising Star',
                'description': 'Earned 1000 points',
                'icon': 'star-fill',
                'points_required': 1000,
                'color': 'warning'
            },
            {
                'name': 'Master Learner',
                'description': 'Earned 5000 points',
                'icon': 'trophy',
                'points_required': 5000,
                'color': 'success'
            },
            {
                'name': 'Fire Streak',
                'description': 'Maintained a 7-day learning streak',
                'icon': 'fire',
                'points_required': 0,
                'color': 'danger'
            },
        ]

        for badge_data in badges:
            Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample badges!'))