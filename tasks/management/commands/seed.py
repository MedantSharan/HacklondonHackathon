from django.core.management.base import BaseCommand, CommandError

from tasks.models import User
from tasks.models import User, Place, Item
import pytz
from faker import Faker
from random import randint, random

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 10
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        self.create_specific_places_and_items()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )

    def create_specific_places_and_items(self):
        # Retrieve or create @johndoe user
        johndoe_user, _ = User.objects.get_or_create(
            username='@johndoe', 
            defaults={
                'email': 'john.doe@example.org',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'Password123'
            }
        )

        # Manually create places and items for @johndoe
        self.create_place_with_items(johndoe_user, 'Home', [
            ('Keys', 3),
            ('Wallet', 2),
            ('Sunglasses', 1)
        ])

        self.create_place_with_items(johndoe_user, 'Office', [
            ('Laptop', 4),
            ('Charger', 5),
            ('Notebook', 2)
        ])

    def create_place_with_items(self, user, place_name, items):
        place, _ = Place.objects.get_or_create(name=place_name, user=user)
        for item_name, forget_count in items:
            Item.objects.get_or_create(name=item_name, place=place, defaults={'forget_count': forget_count})

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
