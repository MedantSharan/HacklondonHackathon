from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tasks.helpers import login_prohibited
from .models import Place, Item
from django.http import JsonResponse
from .forms import PlaceItemForm



@login_required
def dashboard(request):
    """Display the current user's dashboard."""
    
    # Retrieve the current logged-in user
    current_user = request.user
    
    # Retrieve all places
    places = Place.objects.all()
    
    # Pass user and places data to the template
    return render(request, 'dashboard.html', {'user': current_user, 'places': places})

def increment_streak(request):
    if request.method == 'POST':
        current_user = request.user
        current_user.streaks += 1
        current_user.save()

    return redirect('dashboard')


def remember_items(request, place_id):
    user = request.user
    place = get_object_or_404(Place, id=place_id, user=user)
    items = Item.objects.filter(place=place).order_by('-forget_count')

    if request.method == 'POST':
        # Here, you can handle the logic when the user clicks "Good To Go".
        # For example, updating the forget_count of the items, etc.
        return redirect('dashboard')

    return render(request, 'remember_items.html', {
        'place': place,
        'items': items,
    })

def forgot_items(request, place_id):
    place = Place.objects.get(pk=place_id)
    items = Item.objects.filter(place=place)
    
    
    if request.method == 'POST':
        current_user = request.user
        current_user.streaks = 0
        current_user.save()
        item_ids = request.POST.getlist('items[]')
        for item_id in item_ids:
            item = Item.objects.get(pk=item_id)
            item.checked = True
            item.forget_count += 1
            item.save()
        
        return redirect('dashboard')  # Redirect to the dashboard after submission
    
    return render(request, 'forgot_items.html', {'place': place, 'items': items})

def forget_something_else(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        Item.objects.create(name=item_name, place=place)
        return redirect('forgot_items', place_id=place.id)
    return render(request, 'forgot_something_else.html', {'place': place})


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)
    
def add_places_items(request):
    if request.method == 'POST':
        form = PlaceItemForm(request.POST)

        if form.is_valid():
            # Save the data to the database
            form.save_data(request.user)
            # Redirect to a success page or another view
            return redirect('dashboard')

    else:
        form = PlaceItemForm()
    return render(request, 'add_place_items.html', {'form': form})