from django.contrib.auth.views import LoginView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import generic
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Question, Choice, Vote, UserProfile
from .forms import SignUpForm, ProfileUpdateForm, QuestionForm, ChoiceFormSet


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'questions'

    def get_queryset(self):
        now = timezone.now()

        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Question.objects.all().order_by('-pub_date')

        published = Question.objects.filter(pub_date__lte=now)
        active = [q for q in published if q.is_active()]
        return sorted(active, key=lambda q: q.pub_date, reverse=True)

class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_voted'] = Vote.objects.filter(user=self.request.user, question=self.object).exists()
        else:
            context['has_voted'] = False
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_votes = sum(choice.votes for choice in self.object.choice_set.all())
        results = []
        for choice in self.object.choice_set.all():
            percent = round((choice.votes / total_votes) * 100, 1) if total_votes > 0 else 0
            results.append({'choice': choice, 'percent': percent})
        context['results'] = results
        return context


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    if not question.is_active():
        messages.error(request, "Голосование по этому вопросу завершено.")
        return redirect('polls:index')

    if not request.user.is_authenticated:
        messages.error(request, "Для голосования нужно войти в аккаунт.")
        return redirect('polls:login')

    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': 'Пожалуйста, выберите вариант.',
        })

    if Vote.objects.filter(user=request.user, question=question).exists():
        messages.warning(request, "Вы уже голосовали в этом опросе.")
        return redirect('polls:results', pk=question.id)

    selected_choice.votes += 1
    selected_choice.save()

    Vote.objects.create(user=request.user, question=question, choice=selected_choice)
    messages.success(request, "Ваш голос учтён!")

    return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect('polls:index')
    else:
        form = SignUpForm()
    return render(request, 'polls/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'polls/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлён.")
            return redirect('polls:profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
    return render(request, 'polls/edit_profile.html', {'form': form})


@login_required
def delete_profile(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Ваш аккаунт был удалён.")
        return redirect('polls:index')
    return render(request, 'polls/delete_profile.html')

class PollsLoginView(LoginView):
    template_name = 'polls/login.html'

def logout_view(request):
    logout(request)
    return redirect('polls:index')

@login_required
def question_add(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.question_user = request.user
            question.pub_date = timezone.now()
            question.save()

            formset = ChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
                return redirect('polls:index')
            else:
                pass
        else:
            formset = ChoiceFormSet(request.POST)
    else:
        form = QuestionForm(initial={'question_user': request.user})
        formset = ChoiceFormSet()

    context = {
        "form": form, "formset": formset,
    }
    return render(request, 'polls/question_add.html', context)
