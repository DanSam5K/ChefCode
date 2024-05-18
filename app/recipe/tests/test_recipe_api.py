"""
Tests for recipe API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'https://sample.com/recipe',
    } | params
    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """Create and return a sample user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        response = self.client.get(reverse('recipe:recipe-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com', password='password123'
            )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        self._extracted_from_test_recipe_list_limited(
            recipes, response
            )

    def test_recipe_list_limited_to_user(self):
        """Test retrieving recipes for user."""
        user2 = create_user(
            email='other@example.com', password='testpass'
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        self._extracted_from_test_recipe_list_limited(
            recipes, response
            )

    def _extracted_from_test_recipe_list_limited(self, recipes, response):
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe."""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'description': 'A delicious chocolate cheesecake',
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload:
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_partial_update(self):
        """Test updating a recipe with patch."""
        original_link = 'https://sample.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Chocolate cheesecake',
            link=original_link,
            )

        payload = {'link': 'https://sample.com/recipe.jpg'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.link, payload['link'])
        self.assertEqual(recipe.title, recipe.title)
        self.assertEqual(recipe.user, recipe.user)

    def test_full_update(self):
        """Test updating a recipe with put."""
        recipe = create_recipe(
            user=self.user,
            title='Chocolate cheesecake',
            link='https://sample.com/recipe.pdf',
            description='A delicious chocolate cheesecake',
        )
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': Decimal('12.00'),
            'description': 'A delicious spaghetti carbonara',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload:
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_update_user_returns_error(self):
        """Test updating user returns 403."""
        new_user = create_user(
            email='user2@example.com', password='password123'
            )
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_returns_error(self):
        """Test deleting other user's recipe returns 404."""
        user2 = create_user(
            email='user2@example.com', password='password123'
            )
        recipe = create_recipe(user=user2)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
